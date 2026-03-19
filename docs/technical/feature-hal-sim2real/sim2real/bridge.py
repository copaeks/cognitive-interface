"""
Sim-to-Real Bridge Implementation.

This module provides the core sim-to-real bridge functionality:
- Unified interface for sim and real hardware
- Data validation and sanitization
- Graceful degradation
- Performance monitoring
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Literal

import numpy as np
from numpy.typing import NDArray
from scipy import signal

from ..hal.base import (
    AbstractGlove,
    AbstractMicrophoneArray,
    AbstractTransducer,
    CalibrationData,
    GloveInterface,
    GloveSensorData,
    HardwareConfig,
    HardwareMode,
    MicrophoneArray,
    SampleBuffer,
    Transducer,
)


logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validate and sanitize sensor data.
    
    Ensures data quality and detects anomalies in both
    simulation and real hardware data.
    """
    
    def __init__(
        self,
        max_amplitude: float = 1.0,
        max_sample_rate_deviation: float = 0.05,  # 5%
    ) -> None:
        """
        Initialize validator.
        
        Args:
            max_amplitude: Maximum expected amplitude
            max_sample_rate_deviation: Max allowed sample rate deviation
        """
        self._max_amplitude = max_amplitude
        self._max_sr_deviation = max_sample_rate_deviation
        self._violation_count = 0
    
    def validate_audio(
        self,
        data: NDArray[np.float64],
        expected_sample_rate: int,
        actual_sample_rate: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate audio data.
        
        Args:
            data: Audio data to validate
            expected_sample_rate: Expected sample rate
            actual_sample_rate: Actual sample rate (if known)
        
        Returns:
            (is_valid, details)
        """
        issues = []
        
        # Check for NaN/Inf
        if np.any(np.isnan(data)):
            issues.append("Data contains NaN values")
        if np.any(np.isinf(data)):
            issues.append("Data contains Inf values")
        
        # Check amplitude
        max_val = np.max(np.abs(data))
        if max_val > self._max_amplitude:
            issues.append(f"Amplitude {max_val:.3f} exceeds limit {self._max_amplitude}")
        
        # Check for clipping
        if max_val > 0.99 * self._max_amplitude:
            issues.append("Possible clipping detected")
        
        # Check sample rate
        if actual_sample_rate is not None:
            sr_deviation = abs(actual_sample_rate - expected_sample_rate) / expected_sample_rate
            if sr_deviation > self._max_sr_deviation:
                issues.append(f"Sample rate deviation {sr_deviation:.3f} exceeds limit")
        
        # Check for DC offset
        dc_offset = np.mean(data)
        if abs(dc_offset) > 0.1 * self._max_amplitude:
            issues.append(f"Large DC offset: {dc_offset:.3f}")
        
        is_valid = len(issues) == 0
        if not is_valid:
            self._violation_count += 1
        
        return is_valid, {
            "valid": is_valid,
            "issues": issues,
            "max_amplitude": float(max_val),
            "dc_offset": float(dc_offset),
            "violation_count": self._violation_count,
        }
    
    def validate_glove_data(
        self,
        data: GloveSensorData,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate glove sensor data.
        
        Args:
            data: Glove sensor data to validate
        
        Returns:
            (is_valid, details)
        """
        issues = []
        
        # Check flex values
        if np.any(data.flex_values < 0) or np.any(data.flex_values > 1):
            issues.append("Flex values out of range [0, 1]")
        
        # Check pressure values
        if np.any(data.pressure_values < 0):
            issues.append("Negative pressure values")
        
        # Check IMU values
        accel_mag = np.linalg.norm(data.accelerometer)
        if accel_mag < 1.0 or accel_mag > 20.0:  # m/s^2
            issues.append(f"Unreasonable accelerometer magnitude: {accel_mag:.2f}")
        
        gyro_mag = np.linalg.norm(data.gyroscope)
        if gyro_mag > 100.0:  # rad/s (very fast rotation)
            issues.append(f"Unreasonable gyroscope magnitude: {gyro_mag:.2f}")
        
        is_valid = len(issues) == 0
        if not is_valid:
            self._violation_count += 1
        
        return is_valid, {
            "valid": is_valid,
            "issues": issues,
            "accel_magnitude": float(accel_mag),
            "gyro_magnitude": float(gyro_mag),
            "violation_count": self._violation_count,
        }
    
    def sanitize_audio(
        self,
        data: NDArray[np.float64],
        remove_dc: bool = True,
        clip_amplitude: bool = True,
    ) -> NDArray[np.float64]:
        """
        Sanitize audio data.
        
        Args:
            data: Audio data to sanitize
            remove_dc: Remove DC offset
            clip_amplitude: Clip to valid amplitude range
        
        Returns:
            Sanitized data
        """
        result = data.copy()
        
        # Remove NaN/Inf
        result = np.nan_to_num(result, nan=0.0, posinf=self._max_amplitude, neginf=-self._max_amplitude)
        
        # Remove DC
        if remove_dc:
            result = result - np.mean(result, axis=0)
        
        # Clip amplitude
        if clip_amplitude:
            result = np.clip(result, -self._max_amplitude, self._max_amplitude)
        
        return result


class SimRealMapper:
    """
    Map between simulation and real data formats.
    
    Handles differences in data representation between sim and real.
    """
    
    def __init__(self) -> None:
        """Initialize mapper."""
        self._sim_to_real_scale = 1.0
        self._real_to_sim_scale = 1.0
    
    def set_calibration_scale(
        self,
        sim_data: NDArray[np.float64],
        real_data: NDArray[np.float64],
    ) -> None:
        """
        Set scaling factor based on calibration data.
        
        Args:
            sim_data: Data from simulation
            real_data: Data from real hardware
        """
        # Compute RMS ratio
        sim_rms = np.sqrt(np.mean(sim_data ** 2))
        real_rms = np.sqrt(np.mean(real_data ** 2))
        
        if real_rms > 1e-10:
            self._sim_to_real_scale = real_rms / sim_rms
            self._real_to_sim_scale = sim_rms / real_rms
        
        logger.info(f"Sim-to-real scale: {self._sim_to_real_scale:.4f}")
    
    def sim_to_real(self, sim_data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Convert simulation data to real format."""
        return sim_data * self._sim_to_real_scale
    
    def real_to_sim(self, real_data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Convert real data to simulation format."""
        return real_data * self._real_to_sim_scale


class SimulatedMicrophoneArray(AbstractMicrophoneArray):
    """
    Simulated microphone array for testing and development.
    
    Generates synthetic audio data with configurable characteristics.
    """
    
    def __init__(
        self,
        config: HardwareConfig,
        noise_floor_db: float = -60,
        add_realistic_noise: bool = True,
    ) -> None:
        """
        Initialize simulated microphone array.
        
        Args:
            config: Hardware configuration
            noise_floor_db: Noise floor in dB
            add_realistic_noise: Add realistic microphone noise
        """
        super().__init__(config)
        
        self._noise_floor = 10 ** (noise_floor_db / 20)
        self._add_realistic_noise = add_realistic_noise
        
        # Signal generators
        self._signal_sources: list[dict[str, Any]] = []
        
        # Streaming state
        self._streaming = False
        self._start_time: float = 0.0
        self._samples_generated = 0
        
        logger.info(
            f"SimulatedMicrophoneArray: {config.num_channels}ch @ {config.sample_rate}Hz"
        )
    
    def add_signal_source(
        self,
        signal_func: Callable[[NDArray[np.float64]], NDArray[np.float64]],
        position: NDArray[np.float64] | None = None,
        amplitude: float = 1.0,
    ) -> None:
        """
        Add a signal source.
        
        Args:
            signal_func: Function that generates signal given time array
            position: Source position (for spatial simulation)
            amplitude: Source amplitude
        """
        self._signal_sources.append({
            "func": signal_func,
            "position": position,
            "amplitude": amplitude,
        })
    
    def add_tone_source(
        self,
        frequency: float,
        amplitude: float = 0.5,
        position: NDArray[np.float64] | None = None,
    ) -> None:
        """Add a tone source."""
        def tone_func(t: NDArray[np.float64]) -> NDArray[np.float64]:
            return amplitude * np.sin(2 * np.pi * frequency * t)
        
        self.add_signal_source(tone_func, position, amplitude)
    
    def start_stream(self) -> None:
        """Start streaming."""
        self._streaming = True
        self._start_time = time.time()
        logger.info("Simulated stream started")
    
    def stop_stream(self) -> None:
        """Stop streaming."""
        self._streaming = False
        logger.info("Simulated stream stopped")
    
    def _read_raw(self, num_samples: int | None = None) -> NDArray[np.float64]:
        """Generate simulated samples."""
        if num_samples is None:
            num_samples = self._config.buffer_size
        
        # Generate time array
        t_start = self._samples_generated / self._config.sample_rate
        t = t_start + np.arange(num_samples) / self._config.sample_rate
        
        # Generate signals for each channel
        data = np.zeros((num_samples, self._config.num_channels))
        
        for source in self._signal_sources:
            signal = source["func"](t) * source["amplitude"]
            
            # Add to all channels (could add spatial propagation here)
            for ch in range(self._config.num_channels):
                data[:, ch] += signal
        
        # Add noise
        if self._add_realistic_noise:
            # White noise
            noise = np.random.randn(num_samples, self._config.num_channels) * self._noise_floor
            
            # Add some 50/60Hz hum
            hum_freq = 50.0  # Hz
            hum = 0.1 * self._noise_floor * np.sin(2 * np.pi * hum_freq * t)
            data += hum[:, np.newaxis]
            
            data += noise
        
        self._samples_generated += num_samples
        
        return data
    
    def close(self) -> None:
        """Release resources."""
        self.stop_stream()


class SimulatedTransducer(AbstractTransducer):
    """Simulated ultrasonic transducer."""
    
    def __init__(
        self,
        config: HardwareConfig,
        frequency: float = 40000.0,
    ) -> None:
        """Initialize simulated transducer."""
        super().__init__(config, frequency)
        
        self._emission_log: list[dict[str, Any]] = []
        logger.info(f"SimulatedTransducer: {frequency}Hz")
    
    def start(self) -> None:
        """Start emission."""
        self._emitting = True
        logger.info(f"[SIM] Started emission at {self._frequency}Hz")
    
    def stop(self) -> None:
        """Stop emission."""
        self._emitting = False
        logger.info("[SIM] Stopped emission")
    
    def emit_burst(self, duration_ms: float, frequency: float | None = None) -> None:
        """Emit burst."""
        freq = frequency or self._frequency
        logger.info(f"[SIM] Emitting {duration_ms}ms burst at {freq}Hz")
        
        self._emission_log.append({
            "type": "burst",
            "duration_ms": duration_ms,
            "frequency": freq,
            "amplitude": self._amplitude,
            "timestamp": time.time(),
        })
    
    def _emit_signal(self, signal: NDArray[np.float64]) -> None:
        """Emit signal."""
        logger.info(f"[SIM] Emitting signal: {len(signal)} samples")
        self._emission_log.append({
            "type": "signal",
            "length": len(signal),
            "timestamp": time.time(),
        })
    
    def get_emission_log(self) -> list[dict[str, Any]]:
        """Get emission log."""
        return self._emission_log.copy()
    
    def clear_log(self) -> None:
        """Clear emission log."""
        self._emission_log.clear()


class SimulatedGlove(AbstractGlove):
    """Simulated metamaterial glove."""
    
    def __init__(
        self,
        config: HardwareConfig,
        simulate_gestures: bool = True,
    ) -> None:
        """Initialize simulated glove."""
        super().__init__(config)
        
        self._simulate_gestures = simulate_gestures
        self._gesture_phase = 0.0
        self._vibration_active = False
        
        logger.info("SimulatedGlove initialized")
    
    def connect(self) -> None:
        """Connect to glove."""
        self._connected = True
        logger.info("[SIM] Glove connected")
    
    def disconnect(self) -> None:
        """Disconnect from glove."""
        self._connected = False
        logger.info("[SIM] Glove disconnected")
    
    def _read_raw_sensors(self) -> dict[str, NDArray[np.float64]]:
        """Read simulated sensor data."""
        # Update gesture phase
        self._gesture_phase += 0.05
        
        # Generate flex values (simulating hand opening/closing)
        if self._simulate_gestures:
            base_flex = 0.5 + 0.4 * np.sin(self._gesture_phase)
            flex = np.array([
                base_flex,
                base_flex * 0.95,
                base_flex * 0.9,
                base_flex * 0.85,
                base_flex * 0.8,
            ])
        else:
            flex = np.random.random(self._num_flex)
        
        # Generate pressure (higher when hand is closed)
        is_closed = np.mean(flex) > 0.7
        if is_closed:
            pressure = np.random.random(self._num_pressure) * 50000 + 10000
        else:
            pressure = np.random.random(self._num_pressure) * 500
        
        # Generate IMU data
        accel = np.array([0.0, 0.0, 9.8]) + np.random.randn(3) * 0.1
        gyro = np.random.randn(3) * 0.05
        
        return {
            "flex": np.clip(flex, 0, 1),
            "pressure": pressure,
            "accel": accel,
            "gyro": gyro,
        }
    
    def set_vibration(
        self,
        intensity: float,
        pattern: Literal["continuous", "pulse", "wave"] = "continuous",
    ) -> None:
        """Set vibration."""
        self._vibration_active = intensity > 0
        logger.info(f"[SIM] Vibration: intensity={intensity}, pattern={pattern}")


class Sim2RealBridge:
    """
    Main sim-to-real bridge.
    
    Provides unified interface for both simulation and real hardware.
    Single flag switches between modes.
    
    Example:
        >>> # Simulation mode
        >>> bridge = Sim2RealBridge(mode="sim")
        >>> 
        >>> # Real hardware mode  
        >>> bridge = Sim2RealBridge(mode="real")
        >>> 
        >>> # Same API for both
        >>> mics = bridge.get_microphone_array()
        >>> glove = bridge.get_glove()
    """
    
    def __init__(
        self,
        mode: Literal["sim", "real", "hybrid"] | HardwareMode = "sim",
        config: HardwareConfig | None = None,
        auto_fallback: bool = True,
    ) -> None:
        """
        Initialize sim-to-real bridge.
        
        Args:
            mode: Operation mode ("sim", "real", or "hybrid")
            config: Hardware configuration
            auto_fallback: Automatically fall back to sim on real hardware failure
        """
        if isinstance(mode, str):
            mode_map = {
                "sim": HardwareMode.SIMULATION,
                "real": HardwareMode.REAL,
                "hybrid": HardwareMode.HYBRID,
            }
            self._mode = mode_map.get(mode.lower(), HardwareMode.SIMULATION)
        else:
            self._mode = mode
        
        self._config = config or HardwareConfig()
        self._auto_fallback = auto_fallback
        
        # Components
        self._microphones: MicrophoneArray | None = None
        self._transducer: Transducer | None = None
        self._glove: GloveInterface | None = None
        
        # Validation
        self._validator = DataValidator()
        self._mapper = SimRealMapper()
        
        # Performance monitoring
        self._performance_stats: dict[str, Any] = {}
        
        logger.info(f"Sim2RealBridge initialized: mode={self._mode.name}")
    
    @property
    def mode(self) -> HardwareMode:
        """Current operation mode."""
        return self._mode
    
    def get_microphone_array(self) -> MicrophoneArray:
        """Get microphone array (sim or real)."""
        if self._microphones is None:
            self._microphones = self._create_microphone_array()
        return self._microphones
    
    def get_transducer(self, frequency: float = 40000.0) -> Transducer:
        """Get transducer (sim or real)."""
        if self._transducer is None:
            self._transducer = self._create_transducer(frequency)
        return self._transducer
    
    def get_glove(self) -> GloveInterface:
        """Get glove interface (sim or real)."""
        if self._glove is None:
            self._glove = self._create_glove()
        return self._glove
    
    def _create_microphone_array(self) -> MicrophoneArray:
        """Create microphone array based on mode."""
        from ..hal.factory import HardwareFactory
        
        factory = HardwareFactory(mode=self._mode)
        
        try:
            mics = factory.create_microphone_array(
                self._config,
                fallback_to_sim=self._auto_fallback,
            )
            
            # Wrap with validation
            return ValidatedMicrophoneArray(mics, self._validator)
            
        except Exception as e:
            logger.error(f"Failed to create microphone array: {e}")
            if self._auto_fallback and self._mode != HardwareMode.SIMULATION:
                logger.info("Falling back to simulation")
                return SimulatedMicrophoneArray(self._config)
            raise
    
    def _create_transducer(self, frequency: float) -> Transducer:
        """Create transducer based on mode."""
        from ..hal.factory import HardwareFactory
        
        factory = HardwareFactory(mode=self._mode)
        
        try:
            return factory.create_transducer(
                self._config,
                frequency,
                fallback_to_sim=self._auto_fallback,
            )
        except Exception as e:
            logger.error(f"Failed to create transducer: {e}")
            if self._auto_fallback and self._mode != HardwareMode.SIMULATION:
                logger.info("Falling back to simulation")
                return SimulatedTransducer(self._config, frequency)
            raise
    
    def _create_glove(self) -> GloveInterface:
        """Create glove interface based on mode."""
        from ..hal.factory import HardwareFactory
        
        factory = HardwareFactory(mode=self._mode)
        
        try:
            return factory.create_glove(
                self._config,
                fallback_to_sim=self._auto_fallback,
            )
        except Exception as e:
            logger.error(f"Failed to create glove: {e}")
            if self._auto_fallback and self._mode != HardwareMode.SIMULATION:
                logger.info("Falling back to simulation")
                return SimulatedGlove(self._config)
            raise
    
    def validate_data(
        self,
        audio_data: NDArray[np.float64] | None = None,
        glove_data: GloveSensorData | None = None,
    ) -> dict[str, Any]:
        """
        Validate data from hardware.
        
        Args:
            audio_data: Audio data to validate
            glove_data: Glove data to validate
        
        Returns:
            Validation results
        """
        results = {}
        
        if audio_data is not None:
            is_valid, details = self._validator.validate_audio(
                audio_data,
                self._config.sample_rate,
            )
            results["audio"] = {"valid": is_valid, **details}
        
        if glove_data is not None:
            is_valid, details = self._validator.validate_glove_data(glove_data)
            results["glove"] = {"valid": is_valid, **details}
        
        return results
    
    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats.copy()
    
    def close(self) -> None:
        """Release all resources."""
        logger.info("Closing Sim2RealBridge")
        
        if self._microphones:
            self._microphones.close()
        if self._transducer:
            self._transducer.close()
        if self._glove:
            self._glove.close()


class ValidatedMicrophoneArray:
    """
    Wrapper that adds validation to microphone array.
    
    Automatically validates and sanitizes all data.
    """
    
    def __init__(
        self,
        microphone_array: MicrophoneArray,
        validator: DataValidator,
    ) -> None:
        """Initialize validated wrapper."""
        self._mics = microphone_array
        self._validator = validator
        self._validation_stats = {"valid_reads": 0, "invalid_reads": 0}
    
    def __getattr__(self, name: str) -> Any:
        """Delegate to wrapped object."""
        return getattr(self._mics, name)
    
    def read(self, num_samples: int | None = None) -> SampleBuffer:
        """Read with validation."""
        samples = self._mics.read(num_samples)
        
        # Validate
        is_valid, details = self._validator.validate_audio(
            samples.data,
            self._mics.sample_rate,
        )
        
        if is_valid:
            self._validation_stats["valid_reads"] += 1
        else:
            self._validation_stats["invalid_reads"] += 1
            logger.warning(f"Invalid audio data: {details['issues']}")
            
            # Sanitize
            samples.data = self._validator.sanitize_audio(samples.data)
        
        return samples
    
    def get_validation_stats(self) -> dict[str, int]:
        """Get validation statistics."""
        return self._validation_stats.copy()
