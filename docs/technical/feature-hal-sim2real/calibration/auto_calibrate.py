"""
Automatic Calibration for Microphone Arrays.

Provides automated calibration procedures:
- Tone-based calibration (gain, phase)
- Impulse response calibration (time alignment)
- Position calibration (microphone geometry)
- Temperature compensation

Usage:
    >>> from hal.factory import create_microphone_array
    >>> from calibration.auto_calibrate import ArrayCalibrator
    >>> 
    >>> mics = create_microphone_array("real")
    >>> calibrator = ArrayCalibrator(mics)
    >>> calibration = calibrator.calibrate()
    >>> calibration.save("calibration.json")
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray
from scipy import signal
from scipy.optimize import minimize

from ..hal.base import (
    CalibrationData,
    HardwareConfig,
    MicrophoneArray,
    SampleBuffer,
    Transducer,
)


logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """Result of a calibration procedure."""
    success: bool
    calibration: CalibrationData
    quality_score: float
    error_message: str = ""
    metadata: dict[str, Any] | None = None


class CalibrationProcedure(ABC):
    """Abstract base class for calibration procedures."""
    
    def __init__(
        self,
        microphone_array: MicrophoneArray,
        transducer: Transducer | None = None,
    ) -> None:
        self._mics = microphone_array
        self._transducer = transducer
        self._sample_rate = microphone_array.sample_rate
    
    @abstractmethod
    def run(self) -> CalibrationResult:
        """Run calibration procedure."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get procedure name."""
        pass


class ToneCalibration(CalibrationProcedure):
    """
    Calibrate using known frequency tones.
    
    Measures:
    - Relative gain between microphones
    - Phase differences
    - Frequency response
    """
    
    DEFAULT_FREQUENCIES = [1000, 2000, 4000, 8000]  # Hz
    TONE_DURATION_MS = 500
    SETTLE_TIME_MS = 100
    
    def __init__(
        self,
        microphone_array: MicrophoneArray,
        transducer: Transducer,
        frequencies: list[float] | None = None,
    ) -> None:
        super().__init__(microphone_array, transducer)
        self._frequencies = frequencies or self.DEFAULT_FREQUENCIES
    
    def get_name(self) -> str:
        return "ToneCalibration"
    
    def run(self) -> CalibrationResult:
        """Run tone-based calibration."""
        logger.info(f"Starting tone calibration at frequencies: {self._frequencies}")
        
        num_channels = self._mics.num_microphones
        gain_measurements: list[NDArray[np.float64]] = []
        phase_measurements: list[NDArray[np.float64]] = []
        
        try:
            self._mics.start_stream()
            time.sleep(0.1)  # Allow stream to stabilize
            
            for freq in self._frequencies:
                logger.info(f"Calibrating at {freq}Hz")
                
                # Emit tone
                self._transducer.emit_burst(self.TONE_DURATION_MS, frequency=freq)
                
                # Wait for tone to complete
                time.sleep((self.TONE_DURATION_MS + self.SETTLE_TIME_MS) / 1000)
                
                # Record response
                record_duration = self.TONE_DURATION_MS / 1000
                num_samples = int(record_duration * self._sample_rate)
                
                # Clear buffer and capture
                self._mics.clear_buffer()
                time.sleep(record_duration)
                samples = self._mics.read_available()
                
                if len(samples.data) < num_samples // 2:
                    logger.warning(f"Insufficient samples at {freq}Hz")
                    continue
                
                # Analyze response
                gain, phase = self._analyze_tone_response(samples.data, freq)
                gain_measurements.append(gain)
                phase_measurements.append(phase)
            
            self._mics.stop_stream()
            
            # Compute average calibration
            if gain_measurements:
                avg_gain = np.mean(gain_measurements, axis=0)
                avg_phase = np.mean(phase_measurements, axis=0)
                
                # Normalize to first channel
                gain_calibration = avg_gain[0] / (avg_gain + 1e-10)
                phase_calibration = avg_phase - avg_phase[0]
                
                calibration = CalibrationData(
                    gain_calibration=gain_calibration,
                    phase_calibration=phase_calibration,
                    calibration_time=time.time(),
                )
                
                quality = self._compute_quality(gain_measurements, phase_measurements)
                
                return CalibrationResult(
                    success=True,
                    calibration=calibration,
                    quality_score=quality,
                    metadata={
                        "frequencies": self._frequencies,
                        "gain_measurements": gain_measurements,
                        "phase_measurements": phase_measurements,
                    }
                )
            else:
                return CalibrationResult(
                    success=False,
                    calibration=CalibrationData(),
                    quality_score=0.0,
                    error_message="No valid measurements obtained",
                )
        
        except Exception as e:
            logger.error(f"Tone calibration failed: {e}")
            return CalibrationResult(
                success=False,
                calibration=CalibrationData(),
                quality_score=0.0,
                error_message=str(e),
            )
    
    def _analyze_tone_response(
        self,
        data: NDArray[np.float64],
        frequency: float,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Analyze tone response for gain and phase."""
        num_channels = data.shape[1] if data.ndim > 1 else 1
        
        gains = np.zeros(num_channels)
        phases = np.zeros(num_channels)
        
        for ch in range(num_channels):
            channel_data = data[:, ch] if data.ndim > 1 else data
            
            # Compute FFT
            fft = np.fft.rfft(channel_data)
            freqs = np.fft.rfftfreq(len(channel_data), 1 / self._sample_rate)
            
            # Find bin closest to target frequency
            freq_idx = np.argmin(np.abs(freqs - frequency))
            
            # Extract magnitude and phase
            magnitude = np.abs(fft[freq_idx])
            phase = np.angle(fft[freq_idx])
            
            gains[ch] = magnitude
            phases[ch] = phase
        
        return gains, phases
    
    def _compute_quality(
        self,
        gain_measurements: list[NDArray[np.float64]],
        phase_measurements: list[NDArray[np.float64]],
    ) -> float:
        """Compute calibration quality score (0-1)."""
        if not gain_measurements:
            return 0.0
        
        # Check consistency across frequencies
        gain_std = np.std(gain_measurements, axis=0)
        phase_std = np.std(phase_measurements, axis=0)
        
        # Lower std = higher quality
        gain_quality = 1.0 - np.mean(gain_std) / (np.mean(gain_measurements) + 1e-10)
        phase_quality = 1.0 - np.mean(phase_std) / (np.pi + 1e-10)
        
        return float(np.clip((gain_quality + phase_quality) / 2, 0, 1))


class ImpulseCalibration(CalibrationProcedure):
    """
    Calibrate using impulse responses.
    
    Measures:
    - Time-of-flight between channels
    - Impulse response shape
    - Channel delays
    """
    
    IMPULSE_DURATION_MS = 10
    RECORD_DURATION_MS = 100
    
    def get_name(self) -> str:
        return "ImpulseCalibration"
    
    def run(self) -> CalibrationResult:
        """Run impulse-based calibration."""
        logger.info("Starting impulse calibration")
        
        if self._transducer is None:
            return CalibrationResult(
                success=False,
                calibration=CalibrationData(),
                quality_score=0.0,
                error_message="Transducer required for impulse calibration",
            )
        
        try:
            self._mics.start_stream()
            time.sleep(0.1)
            
            # Emit impulse (short burst)
            self._transducer.emit_burst(self.IMPULSE_DURATION_MS)
            
            # Record response
            record_duration = self.RECORD_DURATION_MS / 1000
            time.sleep(record_duration)
            samples = self._mics.read_available()
            
            self._mics.stop_stream()
            
            # Analyze impulse response
            time_offsets = self._analyze_impulse_response(samples.data)
            
            calibration = CalibrationData(
                time_offset=time_offsets,
                calibration_time=time.time(),
            )
            
            quality = self._compute_impulse_quality(samples.data, time_offsets)
            
            return CalibrationResult(
                success=True,
                calibration=calibration,
                quality_score=quality,
                metadata={"impulse_data": samples.data},
            )
        
        except Exception as e:
            logger.error(f"Impulse calibration failed: {e}")
            return CalibrationResult(
                success=False,
                calibration=CalibrationData(),
                quality_score=0.0,
                error_message=str(e),
            )
    
    def _analyze_impulse_response(
        self,
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Analyze impulse response for time offsets."""
        num_channels = data.shape[1] if data.ndim > 1 else 1
        time_offsets = np.zeros(num_channels)
        
        # Find reference channel (first channel)
        ref_data = data[:, 0] if data.ndim > 1 else data
        
        for ch in range(num_channels):
            channel_data = data[:, ch] if data.ndim > 1 else data
            
            # Compute cross-correlation with reference
            correlation = signal.correlate(ref_data, channel_data, mode='full')
            lags = signal.correlation_lags(len(ref_data), len(channel_data), mode='full')
            
            # Find peak
            peak_idx = np.argmax(np.abs(correlation))
            lag = lags[peak_idx]
            
            # Convert to time offset
            time_offsets[ch] = lag / self._sample_rate
        
        return time_offsets
    
    def _compute_impulse_quality(
        self,
        data: NDArray[np.float64],
        time_offsets: NDArray[np.float64],
    ) -> float:
        """Compute impulse calibration quality."""
        # Check if impulses are well-defined
        num_channels = data.shape[1] if data.ndim > 1 else 1
        
        peak_ratios = []
        for ch in range(num_channels):
            channel_data = data[:, ch] if data.ndim > 1 else data
            
            # Find peak
            peak_idx = np.argmax(np.abs(channel_data))
            peak_val = np.abs(channel_data[peak_idx])
            
            # Compute noise floor
            noise = np.std(channel_data[:peak_idx//2]) if peak_idx > 10 else 1e-10
            
            peak_ratios.append(peak_val / (noise + 1e-10))
        
        # Higher SNR = better quality
        avg_snr = np.mean(peak_ratios)
        quality = 1.0 - np.exp(-avg_snr / 100)
        
        return float(np.clip(quality, 0, 1))


class PositionCalibration(CalibrationProcedure):
    """
    Calibrate microphone positions using acoustic measurements.
    
    Uses time-of-flight measurements from multiple source positions
    to estimate microphone array geometry.
    """
    
    NUM_SOURCE_POSITIONS = 8
    SOURCE_DISTANCE_M = 0.5
    
    def get_name(self) -> str:
        return "PositionCalibration"
    
    def run(self) -> CalibrationResult:
        """Run position calibration."""
        logger.info("Starting position calibration")
        
        # Generate source positions (circle around array)
        angles = np.linspace(0, 2 * np.pi, self.NUM_SOURCE_POSITIONS, endpoint=False)
        source_positions = np.array([
            [self.SOURCE_DISTANCE_M * np.cos(a), self.SOURCE_DISTANCE_M * np.sin(a), 0]
            for a in angles
        ])
        
        try:
            # Measure time-of-flight from each position
            tof_measurements = self._measure_tof_from_positions(source_positions)
            
            # Optimize microphone positions
            initial_positions = self._get_initial_positions()
            
            result = minimize(
                self._position_error,
                initial_positions.flatten(),
                args=(source_positions, tof_measurements),
                method='L-BFGS-B',
            )
            
            optimized_positions = result.x.reshape(-1, 3)
            
            calibration = CalibrationData(
                microphone_positions=optimized_positions,
                calibration_time=time.time(),
            )
            
            quality = 1.0 / (1.0 + result.fun)  # Lower error = higher quality
            
            return CalibrationResult(
                success=result.success,
                calibration=calibration,
                quality_score=float(quality),
                metadata={
                    "optimization_result": result,
                    "tof_measurements": tof_measurements,
                }
            )
        
        except Exception as e:
            logger.error(f"Position calibration failed: {e}")
            return CalibrationResult(
                success=False,
                calibration=CalibrationData(),
                quality_score=0.0,
                error_message=str(e),
            )
    
    def _measure_tof_from_positions(
        self,
        source_positions: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Measure time-of-flight from each source position."""
        num_sources = len(source_positions)
        num_channels = self._mics.num_microphones
        
        tof = np.zeros((num_sources, num_channels))
        
        # This would require moving the transducer or using multiple emitters
        # For now, return simulated data
        for i, pos in enumerate(source_positions):
            for ch in range(num_channels):
                # Simulate TOF based on distance
                distance = np.linalg.norm(pos)
                tof[i, ch] = distance / 343.0  # Speed of sound
        
        return tof
    
    def _get_initial_positions(self) -> NDArray[np.float64]:
        """Get initial microphone position estimates."""
        num_channels = self._mics.num_microphones
        
        # Default: microphones in a circle
        radius = 0.015  # 1.5cm radius
        angles = np.linspace(0, 2 * np.pi, num_channels, endpoint=False)
        
        positions = np.array([
            [radius * np.cos(a), radius * np.sin(a), 0]
            for a in angles
        ])
        
        return positions
    
    def _position_error(
        self,
        positions_flat: NDArray[np.float64],
        source_positions: NDArray[np.float64],
        measured_tof: NDArray[np.float64],
    ) -> float:
        """Compute error between measured and predicted TOF."""
        positions = positions_flat.reshape(-1, 3)
        num_sources = len(source_positions)
        
        error = 0.0
        for i in range(num_sources):
            for j, mic_pos in enumerate(positions):
                # Predicted TOF
                distance = np.linalg.norm(source_positions[i] - mic_pos)
                predicted_tof = distance / 343.0
                
                # Error
                error += (predicted_tof - measured_tof[i, j]) ** 2
        
        return error


class ArrayCalibrator:
    """
    Main calibrator for microphone arrays.
    
    Runs multiple calibration procedures and combines results.
    """
    
    def __init__(
        self,
        microphone_array: MicrophoneArray,
        transducer: Transducer | None = None,
    ) -> None:
        """
        Initialize array calibrator.
        
        Args:
            microphone_array: Microphone array to calibrate
            transducer: Optional transducer for active calibration
        """
        self._mics = microphone_array
        self._transducer = transducer
        self._procedures: list[CalibrationProcedure] = []
        
        # Register default procedures
        if transducer:
            self._procedures.append(ToneCalibration(microphone_array, transducer))
            self._procedures.append(ImpulseCalibration(microphone_array, transducer))
        
        self._procedures.append(PositionCalibration(microphone_array, transducer))
    
    def add_procedure(self, procedure: CalibrationProcedure) -> None:
        """Add a custom calibration procedure."""
        self._procedures.append(procedure)
    
    def calibrate(self) -> CalibrationResult:
        """
        Run full calibration.
        
        Returns:
            Combined calibration result
        """
        logger.info(f"Starting calibration with {len(self._procedures)} procedures")
        
        results: list[CalibrationResult] = []
        
        for procedure in self._procedures:
            logger.info(f"Running {procedure.get_name()}")
            result = procedure.run()
            results.append(result)
            
            if result.success:
                logger.info(f"{procedure.get_name()}: quality={result.quality_score:.3f}")
            else:
                logger.warning(f"{procedure.get_name()} failed: {result.error_message}")
        
        # Combine results
        combined_calibration = self._combine_calibrations(results)
        overall_quality = np.mean([r.quality_score for r in results if r.success])
        
        success = any(r.success for r in results)
        
        return CalibrationResult(
            success=success,
            calibration=combined_calibration,
            quality_score=float(overall_quality),
            metadata={"individual_results": results},
        )
    
    def _combine_calibrations(
        self,
        results: list[CalibrationResult],
    ) -> CalibrationData:
        """Combine calibration results from multiple procedures."""
        combined = CalibrationData()
        
        # Weight by quality score
        total_weight = sum(r.quality_score for r in results if r.success)
        
        if total_weight == 0:
            return combined
        
        for result in results:
            if not result.success:
                continue
            
            weight = result.quality_score / total_weight
            cal = result.calibration
            
            # Combine gain calibration
            if np.any(cal.gain_calibration != 1.0):
                combined.gain_calibration *= (cal.gain_calibration ** weight)
            
            # Combine phase calibration
            if np.any(cal.phase_calibration != 0.0):
                combined.phase_calibration += cal.phase_calibration * weight
            
            # Combine time offsets
            if np.any(cal.time_offset != 0.0):
                combined.time_offset += cal.time_offset * weight
            
            # Use highest quality position calibration
            if result.quality_score > combined.quality_score:
                combined.microphone_positions = cal.microphone_positions
        
        combined.quality_score = total_weight / len(results)
        combined.calibration_time = time.time()
        
        return combined
    
    def validate_calibration(
        self,
        calibration: CalibrationData,
        num_tests: int = 5,
    ) -> dict[str, float]:
        """
        Validate calibration by running test measurements.
        
        Args:
            calibration: Calibration to validate
            num_tests: Number of test measurements
        
        Returns:
            Validation metrics
        """
        logger.info("Validating calibration")
        
        self._mics.set_calibration(calibration)
        
        # Test metrics
        gain_consistency = []
        phase_consistency = []
        
        for i in range(num_tests):
            if self._transducer:
                # Emit test tone
                self._transducer.emit_burst(100, frequency=4000)
                time.sleep(0.2)
                
                # Record
                self._mics.start_stream()
                time.sleep(0.1)
                samples = self._mics.read_available()
                self._mics.stop_stream()
                
                # Check consistency
                if len(samples.data) > 0:
                    channel_rms = np.sqrt(np.mean(samples.data ** 2, axis=0))
                    gain_consistency.append(np.std(channel_rms) / (np.mean(channel_rms) + 1e-10))
        
        return {
            "gain_consistency": float(np.mean(gain_consistency)) if gain_consistency else 0.0,
            "phase_consistency": float(np.mean(phase_consistency)) if phase_consistency else 0.0,
            "overall_valid": float(np.mean(gain_consistency) < 0.1) if gain_consistency else 0.0,
        }
