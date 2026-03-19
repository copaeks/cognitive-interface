"""
Base Hardware Abstraction Layer Interfaces.

Provides abstract base classes for all hardware components with full type hints
and support for both simulation and real hardware modes.
"""

from __future__ import annotations

import abc
import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    Literal,
    Protocol,
    TypeVar,
    runtime_checkable,
)
from numpy.typing import NDArray
from pathlib import Path
import json
import time


class HardwareMode(Enum):
    """Hardware operation mode."""
    SIMULATION = auto()
    REAL = auto()
    HYBRID = auto()  # Mix of sim and real for testing


@dataclass(frozen=True)
class HardwareConfig:
    """Configuration for hardware components."""
    sample_rate: int = 48000
    buffer_size: int = 1024
    num_channels: int = 4
    bit_depth: int = 24
    
    # Timing
    frame_duration_ms: float = 20.0
    max_latency_ms: float = 5.0
    
    # Calibration
    calibration_file: Path | None = None
    auto_calibrate: bool = True
    
    # Hardware-specific
    i2s_bus: int = 0
    pwm_pin: int = 18
    gpio_chip: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "num_channels": self.num_channels,
            "bit_depth": self.bit_depth,
            "frame_duration_ms": self.frame_duration_ms,
            "max_latency_ms": self.max_latency_ms,
            "calibration_file": str(self.calibration_file) if self.calibration_file else None,
            "auto_calibrate": self.auto_calibrate,
            "i2s_bus": self.i2s_bus,
            "pwm_pin": self.pwm_pin,
            "gpio_chip": self.gpio_chip,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HardwareConfig:
        """Create from dictionary."""
        cfg = data.copy()
        if cfg.get("calibration_file"):
            cfg["calibration_file"] = Path(cfg["calibration_file"])
        return cls(**{k: v for k, v in cfg.items() if k in cls.__dataclass_fields__})


@dataclass
class CalibrationData:
    """Calibration data for microphone arrays."""
    # Gain calibration per channel (linear scale)
    gain_calibration: NDArray[np.float64] = field(default_factory=lambda: np.ones(4))
    
    # Time offset per channel (seconds)
    time_offset: NDArray[np.float64] = field(default_factory=lambda: np.zeros(4))
    
    # Phase calibration per channel (radians)
    phase_calibration: NDArray[np.float64] = field(default_factory=lambda: np.zeros(4))
    
    # Microphone positions (meters, relative to array center)
    microphone_positions: NDArray[np.float64] = field(
        default_factory=lambda: np.array([
            [0.015, 0.0, 0.0],   # Mic 0: right
            [0.0, 0.015, 0.0],   # Mic 1: front
            [-0.015, 0.0, 0.0],  # Mic 2: left
            [0.0, -0.015, 0.0],  # Mic 3: back
        ])
    )
    
    # Uncertainty estimates
    gain_uncertainty: NDArray[np.float64] = field(default_factory=lambda: np.zeros(4))
    time_uncertainty: NDArray[np.float64] = field(default_factory=lambda: np.zeros(4))
    position_uncertainty: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros((4, 3))
    )
    
    # Calibration timestamp
    calibration_time: float = field(default_factory=time.time)
    
    # Calibration quality score (0-1)
    quality_score: float = 0.0
    
    # Valid temperature range for this calibration
    valid_temperature_range: tuple[float, float] = (-10.0, 50.0)
    
    def __post_init__(self) -> None:
        """Validate calibration data shapes."""
        n_channels = len(self.gain_calibration)
        assert self.time_offset.shape == (n_channels,), "Time offset shape mismatch"
        assert self.phase_calibration.shape == (n_channels,), "Phase calibration shape mismatch"
        assert self.microphone_positions.shape == (n_channels, 3), "Position shape mismatch"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "gain_calibration": self.gain_calibration.tolist(),
            "time_offset": self.time_offset.tolist(),
            "phase_calibration": self.phase_calibration.tolist(),
            "microphone_positions": self.microphone_positions.tolist(),
            "gain_uncertainty": self.gain_uncertainty.tolist(),
            "time_uncertainty": self.time_uncertainty.tolist(),
            "position_uncertainty": self.position_uncertainty.tolist(),
            "calibration_time": self.calibration_time,
            "quality_score": self.quality_score,
            "valid_temperature_range": self.valid_temperature_range,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationData:
        """Create from dictionary."""
        return cls(
            gain_calibration=np.array(data["gain_calibration"]),
            time_offset=np.array(data["time_offset"]),
            phase_calibration=np.array(data["phase_calibration"]),
            microphone_positions=np.array(data["microphone_positions"]),
            gain_uncertainty=np.array(data.get("gain_uncertainty", [])),
            time_uncertainty=np.array(data.get("time_uncertainty", [])),
            position_uncertainty=np.array(data.get("position_uncertainty", [])),
            calibration_time=data.get("calibration_time", time.time()),
            quality_score=data.get("quality_score", 0.0),
            valid_temperature_range=tuple(data.get("valid_temperature_range", (-10.0, 50.0))),
        )
    
    def save(self, path: Path) -> None:
        """Save calibration to file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> CalibrationData:
        """Load calibration from file."""
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


@dataclass
class SampleBuffer:
    """Buffer for audio samples with metadata."""
    data: NDArray[np.float64]  # Shape: (n_samples, n_channels) or (n_samples,)
    sample_rate: int
    timestamp: float = field(default_factory=time.time)
    channel_map: list[int] | None = None
    
    def __post_init__(self) -> None:
        """Ensure data is 2D."""
        if self.data.ndim == 1:
            self.data = self.data.reshape(-1, 1)
    
    @property
    def n_samples(self) -> int:
        """Number of samples."""
        return self.data.shape[0]
    
    @property
    def n_channels(self) -> int:
        """Number of channels."""
        return self.data.shape[1]
    
    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.n_samples / self.sample_rate
    
    def get_channel(self, channel: int) -> NDArray[np.float64]:
        """Get single channel data."""
        if self.channel_map:
            channel = self.channel_map[channel]
        return self.data[:, channel]
    
    def slice_time(self, start_sec: float, end_sec: float) -> SampleBuffer:
        """Extract time slice."""
        start_idx = int(start_sec * self.sample_rate)
        end_idx = int(end_sec * self.sample_rate)
        return SampleBuffer(
            data=self.data[start_idx:end_idx],
            sample_rate=self.sample_rate,
            timestamp=self.timestamp + start_sec,
            channel_map=self.channel_map,
        )


@runtime_checkable
class MicrophoneArray(Protocol):
    """Protocol for microphone array implementations."""
    
    @property
    def num_microphones(self) -> int:
        """Number of microphones in array."""
        ...
    
    @property
    def sample_rate(self) -> int:
        """Sample rate in Hz."""
        ...
    
    @property
    def is_streaming(self) -> bool:
        """Whether currently streaming."""
        ...
    
    @property
    def calibration(self) -> CalibrationData | None:
        """Current calibration data."""
        ...
    
    def start_stream(self) -> None:
        """Start audio streaming."""
        ...
    
    def stop_stream(self) -> None:
        """Stop audio streaming."""
        ...
    
    def read(self, num_samples: int | None = None) -> SampleBuffer:
        """Read samples from buffer."""
        ...
    
    def read_available(self) -> SampleBuffer:
        """Read all available samples."""
        ...
    
    def apply_calibration(self, data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply calibration to raw data."""
        ...
    
    def set_calibration(self, calibration: CalibrationData) -> None:
        """Set calibration data."""
        ...
    
    def clear_buffer(self) -> None:
        """Clear internal buffer."""
        ...
    
    def close(self) -> None:
        """Release resources."""
        ...


@runtime_checkable
class Transducer(Protocol):
    """Protocol for ultrasonic transducer/emitter implementations."""
    
    @property
    def frequency(self) -> float:
        """Operating frequency in Hz."""
        ...
    
    @property
    def is_emitting(self) -> bool:
        """Whether currently emitting."""
        ...
    
    def start(self) -> None:
        """Start emission."""
        ...
    
    def stop(self) -> None:
        """Stop emission."""
        ...
    
    def set_frequency(self, frequency: float) -> None:
        """Set emission frequency."""
        ...
    
    def set_amplitude(self, amplitude: float) -> None:
        """Set emission amplitude (0-1)."""
        ...
    
    def emit_burst(self, duration_ms: float, frequency: float | None = None) -> None:
        """Emit a single burst."""
        ...
    
    def emit_chirp(
        self,
        start_freq: float,
        end_freq: float,
        duration_ms: float,
        amplitude: float = 1.0,
    ) -> None:
        """Emit frequency sweep."""
        ...
    
    def close(self) -> None:
        """Release resources."""
        ...


@dataclass
class GloveSensorData:
    """Data from glove sensors."""
    # Flex sensor values (0-1, normalized)
    flex_values: NDArray[np.float64]
    
    # Pressure sensor values (Pascals)
    pressure_values: NDArray[np.float64]
    
    # IMU data (accelerometer in m/s^2, gyroscope in rad/s)
    accelerometer: NDArray[np.float64]  # Shape: (3,)
    gyroscope: NDArray[np.float64]       # Shape: (3,)
    
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    # Sensor positions (for metamaterial elements)
    sensor_positions: NDArray[np.float64] | None = None  # Shape: (n_sensors, 3)


@runtime_checkable
class GloveInterface(Protocol):
    """Protocol for metamaterial glove implementations."""
    
    @property
    def num_flex_sensors(self) -> int:
        """Number of flex sensors."""
        ...
    
    @property
    def num_pressure_sensors(self) -> int:
        """Number of pressure sensors."""
        ...
    
    @property
    def has_imu(self) -> bool:
        """Whether glove has IMU."""
        ...
    
    @property
    def is_connected(self) -> bool:
        """Whether glove is connected."""
        ...
    
    def connect(self) -> None:
        """Connect to glove."""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from glove."""
        ...
    
    def read_sensors(self) -> GloveSensorData:
        """Read all sensor data."""
        ...
    
    def get_flex(self) -> NDArray[np.float64]:
        """Get flex sensor readings."""
        ...
    
    def get_pressure(self) -> NDArray[np.float64]:
        """Get pressure sensor readings."""
        ...
    
    def get_imu(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get IMU readings (accel, gyro)."""
        ...
    
    def set_vibration(
        self,
        intensity: float,
        pattern: Literal["continuous", "pulse", "wave"] = "continuous",
    ) -> None:
        """Set haptic feedback."""
        ...
    
    def calibrate(self) -> None:
        """Calibrate sensors."""
        ...
    
    def close(self) -> None:
        """Release resources."""
        ...


class AbstractMicrophoneArray(abc.ABC):
    """Abstract base class for microphone arrays."""
    
    def __init__(self, config: HardwareConfig) -> None:
        self._config = config
        self._calibration: CalibrationData | None = None
        self._streaming = False
        self._buffer: list[NDArray[np.float64]] = []
        self._buffer_lock = False
    
    @property
    def num_microphones(self) -> int:
        """Number of microphones."""
        return self._config.num_channels
    
    @property
    def sample_rate(self) -> int:
        """Sample rate."""
        return self._config.sample_rate
    
    @property
    def is_streaming(self) -> bool:
        """Streaming status."""
        return self._streaming
    
    @property
    def calibration(self) -> CalibrationData | None:
        """Current calibration."""
        return self._calibration
    
    @abc.abstractmethod
    def start_stream(self) -> None:
        """Start streaming - implement in subclass."""
        pass
    
    @abc.abstractmethod
    def stop_stream(self) -> None:
        """Stop streaming - implement in subclass."""
        pass
    
    @abc.abstractmethod
    def _read_raw(self, num_samples: int | None = None) -> NDArray[np.float64]:
        """Read raw samples - implement in subclass."""
        pass
    
    def read(self, num_samples: int | None = None) -> SampleBuffer:
        """Read calibrated samples."""
        raw = self._read_raw(num_samples)
        calibrated = self.apply_calibration(raw)
        return SampleBuffer(
            data=calibrated,
            sample_rate=self._config.sample_rate,
        )
    
    def read_available(self) -> SampleBuffer:
        """Read all available samples."""
        return self.read(None)
    
    def apply_calibration(self, data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply calibration to raw data."""
        if self._calibration is None:
            return data
        
        # Apply gain calibration
        calibrated = data * self._calibration.gain_calibration
        
        # Apply phase calibration (in frequency domain for accuracy)
        if np.any(self._calibration.phase_calibration != 0):
            calibrated = self._apply_phase_calibration(calibrated)
        
        return calibrated
    
    def _apply_phase_calibration(self, data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply phase calibration using Hilbert transform."""
        from scipy.signal import hilbert
        
        result = np.zeros_like(data)
        for ch in range(data.shape[1] if data.ndim > 1 else 1):
            channel_data = data[:, ch] if data.ndim > 1 else data
            analytic = hilbert(channel_data)
            phase_shift = self._calibration.phase_calibration[ch]
            shifted = np.real(analytic * np.exp(1j * phase_shift))
            if data.ndim > 1:
                result[:, ch] = shifted
            else:
                result = shifted
        
        return result
    
    def set_calibration(self, calibration: CalibrationData) -> None:
        """Set calibration data."""
        self._calibration = calibration
    
    def clear_buffer(self) -> None:
        """Clear internal buffer."""
        self._buffer.clear()
    
    def close(self) -> None:
        """Release resources."""
        if self._streaming:
            self.stop_stream()


class AbstractTransducer(abc.ABC):
    """Abstract base class for transducers."""
    
    def __init__(self, config: HardwareConfig, frequency: float = 40000.0) -> None:
        self._config = config
        self._frequency = frequency
        self._amplitude = 1.0
        self._emitting = False
    
    @property
    def frequency(self) -> float:
        """Current frequency."""
        return self._frequency
    
    @property
    def is_emitting(self) -> bool:
        """Emission status."""
        return self._emitting
    
    @abc.abstractmethod
    def start(self) -> None:
        """Start emission."""
        pass
    
    @abc.abstractmethod
    def stop(self) -> None:
        """Stop emission."""
        pass
    
    def set_frequency(self, frequency: float) -> None:
        """Set frequency."""
        self._frequency = frequency
    
    def set_amplitude(self, amplitude: float) -> None:
        """Set amplitude (0-1)."""
        self._amplitude = np.clip(amplitude, 0.0, 1.0)
    
    @abc.abstractmethod
    def emit_burst(self, duration_ms: float, frequency: float | None = None) -> None:
        """Emit burst."""
        pass
    
    def emit_chirp(
        self,
        start_freq: float,
        end_freq: float,
        duration_ms: float,
        amplitude: float = 1.0,
    ) -> None:
        """Emit frequency sweep."""
        # Default implementation - subclasses may override
        import numpy as np
        from scipy.signal import chirp as scipy_chirp
        
        t = np.linspace(0, duration_ms / 1000, int(self._config.sample_rate * duration_ms / 1000))
        signal = scipy_chirp(t, start_freq, t[-1], end_freq, method='linear')
        signal *= amplitude
        
        # Subclass should implement actual emission
        self._emit_signal(signal)
    
    @abc.abstractmethod
    def _emit_signal(self, signal: NDArray[np.float64]) -> None:
        """Emit signal - implement in subclass."""
        pass
    
    def close(self) -> None:
        """Release resources."""
        if self._emitting:
            self.stop()


class AbstractGlove(abc.ABC):
    """Abstract base class for metamaterial gloves."""
    
    def __init__(self, config: HardwareConfig) -> None:
        self._config = config
        self._connected = False
        self._num_flex = 5  # Default: 5 fingers
        self._num_pressure = 10  # Default: pressure points
        self._has_imu = True
    
    @property
    def num_flex_sensors(self) -> int:
        """Number of flex sensors."""
        return self._num_flex
    
    @property
    def num_pressure_sensors(self) -> int:
        """Number of pressure sensors."""
        return self._num_pressure
    
    @property
    def has_imu(self) -> bool:
        """Has IMU."""
        return self._has_imu
    
    @property
    def is_connected(self) -> bool:
        """Connection status."""
        return self._connected
    
    @abc.abstractmethod
    def connect(self) -> None:
        """Connect to glove."""
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect from glove."""
        pass
    
    @abc.abstractmethod
    def _read_raw_sensors(self) -> dict[str, NDArray[np.float64]]:
        """Read raw sensor data - implement in subclass."""
        pass
    
    def read_sensors(self) -> GloveSensorData:
        """Read all sensors."""
        raw = self._read_raw_sensors()
        return GloveSensorData(
            flex_values=raw.get("flex", np.zeros(self._num_flex)),
            pressure_values=raw.get("pressure", np.zeros(self._num_pressure)),
            accelerometer=raw.get("accel", np.zeros(3)),
            gyroscope=raw.get("gyro", np.zeros(3)),
        )
    
    def get_flex(self) -> NDArray[np.float64]:
        """Get flex readings."""
        return self.read_sensors().flex_values
    
    def get_pressure(self) -> NDArray[np.float64]:
        """Get pressure readings."""
        return self.read_sensors().pressure_values
    
    def get_imu(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get IMU readings."""
        data = self.read_sensors()
        return data.accelerometer, data.gyroscope
    
    @abc.abstractmethod
    def set_vibration(
        self,
        intensity: float,
        pattern: Literal["continuous", "pulse", "wave"] = "continuous",
    ) -> None:
        """Set haptic feedback."""
        pass
    
    def calibrate(self) -> None:
        """Calibrate sensors - default no-op."""
        pass
    
    def close(self) -> None:
        """Release resources."""
        if self._connected:
            self.disconnect()
