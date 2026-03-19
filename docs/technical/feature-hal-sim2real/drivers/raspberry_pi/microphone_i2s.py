"""
I2S Microphone Array Driver for Raspberry Pi.

Supports 4-channel MEMS microphone arrays using I2S interface.
Optimized for Raspberry Pi 5 with real-time constraints.

Hardware Requirements:
- Raspberry Pi 4/5
- 4x I2S MEMS microphones (e.g., SPH0645, INMP441)
- I2S audio HAT or custom wiring

Wiring ( typical configuration ):
- GPIO 18 (Pin 12): I2S CLK (BCLK)
- GPIO 19 (Pin 35): I2S WS (LRCLK)
- GPIO 20 (Pin 38): I2S DATA IN (DIN)
- GPIO 21 (Pin 40): I2S DATA OUT (DOUT) - if needed

For 4 microphones, use multiplexer or multiple I2S buses.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Callable

import numpy as np
from numpy.typing import NDArray

from ...hal.base import (
    AbstractMicrophoneArray,
    CalibrationData,
    HardwareConfig,
    SampleBuffer,
)


logger = logging.getLogger(__name__)

# Try to import Raspberry Pi specific libraries
try:
    import board
    import busio
    from digitalio import DigitalInOut
    RPI_LIBS_AVAILABLE = True
except ImportError:
    logger.warning("RPi libraries not available - using mock mode")
    RPI_LIBS_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class I2SMicrophoneArray(AbstractMicrophoneArray):
    """
    I2S microphone array driver for Raspberry Pi.
    
    Supports 4-channel MEMS microphones with real-time streaming.
    Uses double-buffering for glitch-free audio capture.
    
    Example:
        >>> config = HardwareConfig(sample_rate=48000, num_channels=4)
        >>> mics = I2SMicrophoneArray(config)
        >>> mics.start_stream()
        >>> data = mics.read(1024)
        >>> mics.stop_stream()
    """
    
    # I2S configuration
    DEFAULT_I2S_PINS = {
        "bclk": 18,   # GPIO 18 (Pin 12)
        "lrclk": 19,  # GPIO 19 (Pin 35)
        "din": 20,    # GPIO 20 (Pin 38)
    }
    
    # Buffer configuration
    RING_BUFFER_SIZE = 10  # seconds of audio
    
    def __init__(
        self,
        config: HardwareConfig,
        i2s_pins: dict[str, int] | None = None,
        use_sounddevice: bool = True,
    ) -> None:
        """
        Initialize I2S microphone array.
        
        Args:
            config: Hardware configuration
            i2s_pins: Optional pin configuration override
            use_sounddevice: Use sounddevice library if available
        """
        super().__init__(config)
        
        self._i2s_pins = i2s_pins or self.DEFAULT_I2S_PINS
        self._use_sounddevice = use_sounddevice and SOUNDDEVICE_AVAILABLE
        
        # Ring buffer for audio data
        self._ring_buffer: deque[NDArray[np.float64]] = deque()
        self._buffer_lock = threading.Lock()
        
        # Streaming state
        self._stream_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._samples_read = 0
        self._buffer_underruns = 0
        self._start_time: float = 0.0
        
        # Hardware interface
        self._i2s_interface: Any = None
        self._audio_stream: Any = None
        
        # Initialize hardware
        self._initialize_hardware()
        
        logger.info(
            f"I2SMicrophoneArray initialized: "
            f"{config.num_channels}ch @ {config.sample_rate}Hz"
        )
    
    def _initialize_hardware(self) -> None:
        """Initialize I2S hardware interface."""
        if not RPI_LIBS_AVAILABLE:
            logger.warning("Running in mock mode - no real hardware")
            return
        
        if self._use_sounddevice:
            self._initialize_sounddevice()
        else:
            self._initialize_native_i2s()
    
    def _initialize_sounddevice(self) -> None:
        """Initialize using sounddevice library."""
        try:
            # Query available devices
            devices = sd.query_devices()
            logger.debug(f"Available audio devices: {devices}")
            
            # Find I2S device (typically named 'hw' or has I2S in name)
            i2s_device = None
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] >= self._config.num_channels:
                    i2s_device = i
                    logger.info(f"Using audio device: {dev['name']}")
                    break
            
            if i2s_device is None:
                logger.warning("No suitable I2S device found, using default")
                i2s_device = sd.default.device[0]
        
        except Exception as e:
            logger.error(f"Failed to initialize sounddevice: {e}")
            self._use_sounddevice = False
    
    def _initialize_native_i2s(self) -> None:
        """Initialize native I2S interface."""
        try:
            # Try to use Adafruit Blinka for I2S
            # This requires additional configuration
            logger.info("Initializing native I2S interface")
            
            # For now, we'll use a placeholder
            # Real implementation would use pigpio or similar
            self._i2s_interface = None
            
        except Exception as e:
            logger.error(f"Failed to initialize native I2S: {e}")
    
    def start_stream(self) -> None:
        """Start audio streaming."""
        if self._streaming:
            logger.warning("Stream already running")
            return
        
        logger.info("Starting I2S audio stream")
        self._stop_event.clear()
        self._start_time = time.time()
        
        if self._use_sounddevice:
            self._start_sounddevice_stream()
        else:
            self._start_native_stream()
        
        self._streaming = True
        logger.info("Audio stream started")
    
    def _start_sounddevice_stream(self) -> None:
        """Start sounddevice-based stream."""
        def callback(indata: NDArray[np.float64], frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            # Convert to float64 if needed
            if indata.dtype != np.float64:
                data = indata.astype(np.float64)
            else:
                data = indata.copy()
            
            # Add to ring buffer
            with self._buffer_lock:
                self._ring_buffer.append(data)
                
                # Limit buffer size
                max_buffers = int(self.RING_BUFFER_SIZE * self._config.sample_rate / self._config.buffer_size)
                while len(self._ring_buffer) > max_buffers:
                    self._ring_buffer.popleft()
                    self._buffer_underruns += 1
        
        self._audio_stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.num_channels,
            dtype=np.float32,
            blocksize=self._config.buffer_size,
            callback=callback,
        )
        self._audio_stream.start()
    
    def _start_native_stream(self) -> None:
        """Start native I2S stream."""
        # Start capture thread
        self._stream_thread = threading.Thread(
            target=self._capture_thread,
            name="I2SCapture",
            daemon=True,
        )
        self._stream_thread.start()
    
    def _capture_thread(self) -> None:
        """Background thread for I2S capture."""
        logger.info("I2S capture thread started")
        
        # Mock implementation - generate synthetic data
        # Real implementation would read from I2S hardware
        samples_per_buffer = self._config.buffer_size
        
        while not self._stop_event.is_set():
            try:
                # In real implementation, read from I2S
                # For now, generate silence
                data = np.zeros((samples_per_buffer, self._config.num_channels), dtype=np.float64)
                
                with self._buffer_lock:
                    self._ring_buffer.append(data)
                
                # Maintain timing
                expected_time = samples_per_buffer / self._config.sample_rate
                time.sleep(expected_time)
                
            except Exception as e:
                logger.error(f"Capture thread error: {e}")
                break
        
        logger.info("I2S capture thread stopped")
    
    def stop_stream(self) -> None:
        """Stop audio streaming."""
        if not self._streaming:
            return
        
        logger.info("Stopping I2S audio stream")
        self._stop_event.set()
        
        if self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None
        
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)
            self._stream_thread = None
        
        self._streaming = False
        
        # Log statistics
        duration = time.time() - self._start_time
        logger.info(
            f"Stream stopped. Duration: {duration:.2f}s, "
            f"Samples: {self._samples_read}, Underruns: {self._buffer_underruns}"
        )
    
    def _read_raw(self, num_samples: int | None = None) -> NDArray[np.float64]:
        """
        Read raw samples from buffer.
        
        Args:
            num_samples: Number of samples to read (None = all available)
        
        Returns:
            Raw audio data as float64 array
        """
        with self._buffer_lock:
            if not self._ring_buffer:
                # Return empty array
                return np.zeros((0, self._config.num_channels), dtype=np.float64)
            
            # Concatenate available buffers
            all_data = np.concatenate(list(self._ring_buffer), axis=0)
            self._ring_buffer.clear()
        
        # Extract requested number of samples
        if num_samples is not None and num_samples < len(all_data):
            result = all_data[:num_samples]
            # Put remaining back
            with self._buffer_lock:
                self._ring_buffer.appendleft(all_data[num_samples:])
        else:
            result = all_data
        
        self._samples_read += len(result)
        return result
    
    def read(self, num_samples: int | None = None) -> SampleBuffer:
        """
        Read calibrated samples.
        
        Args:
            num_samples: Number of samples to read
        
        Returns:
            SampleBuffer with calibrated data
        """
        raw = self._read_raw(num_samples)
        
        if len(raw) == 0:
            return SampleBuffer(
                data=np.zeros((0, self._config.num_channels)),
                sample_rate=self._config.sample_rate,
            )
        
        calibrated = self.apply_calibration(raw)
        return SampleBuffer(
            data=calibrated,
            sample_rate=self._config.sample_rate,
        )
    
    def read_available(self) -> SampleBuffer:
        """Read all available samples."""
        return self.read(None)
    
    def get_stats(self) -> dict[str, float | int]:
        """Get stream statistics."""
        duration = time.time() - self._start_time if self._streaming else 0
        return {
            "streaming": float(self._streaming),
            "duration_sec": duration,
            "samples_read": self._samples_read,
            "buffer_underruns": self._buffer_underruns,
            "sample_rate": self._config.sample_rate,
            "num_channels": self._config.num_channels,
        }
    
    def close(self) -> None:
        """Release resources."""
        logger.info("Closing I2S microphone array")
        self.stop_stream()
        super().close()


class MockI2SMicrophoneArray(I2SMicrophoneArray):
    """
    Mock I2S microphone array for testing without hardware.
    
    Generates synthetic audio signals for testing purposes.
    """
    
    def __init__(
        self,
        config: HardwareConfig,
        signal_generator: Callable[[int, int], NDArray[np.float64]] | None = None,
    ) -> None:
        """
        Initialize mock microphone array.
        
        Args:
            config: Hardware configuration
            signal_generator: Optional function to generate test signals
        """
        # Skip parent __init__ to avoid hardware initialization
        self._config = config
        self._calibration: CalibrationData | None = None
        self._streaming = False
        self._ring_buffer: deque[NDArray[np.float64]] = deque()
        self._buffer_lock = threading.Lock()
        self._stream_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._samples_read = 0
        self._buffer_underruns = 0
        self._start_time: float = 0.0
        self._signal_generator = signal_generator or self._default_signal_generator
        
        logger.info(f"MockI2SMicrophoneArray initialized: {config.num_channels}ch")
    
    def _default_signal_generator(
        self,
        num_samples: int,
        num_channels: int,
    ) -> NDArray[np.float64]:
        """Generate default test signal (sine wave with noise)."""
        t = np.arange(num_samples) / self._config.sample_rate
        
        # Generate different frequencies for each channel
        data = np.zeros((num_samples, num_channels), dtype=np.float64)
        for ch in range(num_channels):
            freq = 1000 * (ch + 1)  # 1kHz, 2kHz, 3kHz, 4kHz
            data[:, ch] = 0.3 * np.sin(2 * np.pi * freq * t)
        
        # Add noise
        data += 0.01 * np.random.randn(num_samples, num_channels)
        
        return data
    
    def _initialize_hardware(self) -> None:
        """No hardware to initialize."""
        pass
    
    def _capture_thread(self) -> None:
        """Generate synthetic data."""
        logger.info("Mock capture thread started")
        
        samples_per_buffer = self._config.buffer_size
        
        while not self._stop_event.is_set():
            try:
                # Generate synthetic data
                data = self._signal_generator(samples_per_buffer, self._config.num_channels)
                
                with self._buffer_lock:
                    self._ring_buffer.append(data)
                
                # Maintain timing
                expected_time = samples_per_buffer / self._config.sample_rate
                time.sleep(expected_time)
                
            except Exception as e:
                logger.error(f"Mock capture thread error: {e}")
                break
        
        logger.info("Mock capture thread stopped")
