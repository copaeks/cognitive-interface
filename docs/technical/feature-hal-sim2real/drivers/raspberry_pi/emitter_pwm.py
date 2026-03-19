"""
PWM Ultrasonic Emitter Driver for Raspberry Pi.

Controls ultrasonic transducers using PWM for precise frequency generation.
Optimized for Raspberry Pi 5 with hardware PWM support.

Hardware Requirements:
- Raspberry Pi 4/5
- Ultrasonic transducer (e.g., 40kHz piezo)
- Drive circuit (MOSFET/amplifier recommended)

Wiring:
- GPIO 18 (Pin 12): PWM0 (recommended, has hardware PWM)
- GPIO 19 (Pin 35): PWM1 (alternative)
- Connect to transducer driver circuit
- Use level shifter if needed (3.3V to 5V)

For multiple emitters, use PWM multiplexing or additional GPIOs.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ...hal.base import AbstractTransducer, HardwareConfig


logger = logging.getLogger(__name__)

# Try to import Raspberry Pi GPIO library
try:
    import RPi.GPIO as GPIO
    RPI_GPIO_AVAILABLE = True
except ImportError:
    logger.warning("RPi.GPIO not available - using mock mode")
    RPI_GPIO_AVAILABLE = False

# Try to import pigpio for hardware PWM
try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    logger.warning("pigpio not available - software PWM only")
    PIGPIO_AVAILABLE = False


class PWMTransducer(AbstractTransducer):
    """
    PWM-based ultrasonic transducer driver for Raspberry Pi.
    
    Supports both hardware PWM (preferred) and software PWM.
    Hardware PWM provides better frequency accuracy and stability.
    
    Example:
        >>> config = HardwareConfig()
        >>> emitter = PWMTransducer(config, frequency=40000)
        >>> emitter.start()  # Start continuous emission
        >>> emitter.emit_burst(100)  # 100ms burst
        >>> emitter.stop()
    """
    
    # PWM configuration
    DEFAULT_PWM_PIN = 18  # GPIO 18 (Pin 12) - Hardware PWM0
    HARDWARE_PWM_PINS = {18, 19}  # Pins with hardware PWM
    
    # PWM parameters
    PWM_FREQUENCY = 1000  # PWM carrier frequency (for software PWM)
    DUTY_CYCLE_RANGE = (0, 100)  # Percentage
    
    def __init__(
        self,
        config: HardwareConfig,
        frequency: float = 40000.0,
        pwm_pin: int | None = None,
        use_hardware_pwm: bool = True,
    ) -> None:
        """
        Initialize PWM transducer.
        
        Args:
            config: Hardware configuration
            frequency: Operating frequency in Hz (default 40kHz)
            pwm_pin: GPIO pin for PWM output
            use_hardware_pwm: Prefer hardware PWM if available
        """
        super().__init__(config, frequency)
        
        self._pwm_pin = pwm_pin or self.DEFAULT_PWM_PIN
        self._use_hardware_pwm = use_hardware_pwm and PIGPIO_AVAILABLE
        self._hardware_pwm = self._pwm_pin in self.HARDWARE_PWM_PINS
        
        # PWM state
        self._pwm_duty = 50  # 50% duty cycle for square wave
        self._pwm_interface: Any = None
        self._pigpio_instance: Any = None
        
        # Burst timing
        self._burst_thread: threading.Thread | None = None
        self._burst_stop_event = threading.Event()
        
        # Statistics
        self._emission_count = 0
        self._total_emission_time = 0.0
        
        # Initialize PWM
        self._initialize_pwm()
        
        logger.info(
            f"PWMTransducer initialized: {frequency}Hz on GPIO{pwm_pin}, "
            f"hardware_pwm={self._use_hardware_pwm}"
        )
    
    def _initialize_pwm(self) -> None:
        """Initialize PWM interface."""
        if not RPI_GPIO_AVAILABLE and not PIGPIO_AVAILABLE:
            logger.warning("No GPIO libraries available - running in mock mode")
            return
        
        if self._use_hardware_pwm and self._hardware_pwm:
            self._initialize_hardware_pwm()
        else:
            self._initialize_software_pwm()
    
    def _initialize_hardware_pwm(self) -> None:
        """Initialize hardware PWM using pigpio."""
        try:
            self._pigpio_instance = pigpio.pi()
            if not self._pigpio_instance.connected:
                logger.warning("pigpio daemon not running, falling back to software PWM")
                self._use_hardware_pwm = False
                self._initialize_software_pwm()
                return
            
            # Set pin as output
            self._pigpio_instance.set_mode(self._pwm_pin, pigpio.OUTPUT)
            
            # Initialize with 0 duty cycle (off)
            self._pigpio_instance.hardware_PWM(self._pwm_pin, 0, 0)
            
            logger.info(f"Hardware PWM initialized on GPIO{self._pwm_pin}")
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware PWM: {e}")
            self._use_hardware_pwm = False
            self._initialize_software_pwm()
    
    def _initialize_software_pwm(self) -> None:
        """Initialize software PWM using RPi.GPIO."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self._pwm_pin, GPIO.OUT)
            
            # Create PWM instance
            self._pwm_interface = GPIO.PWM(self._pwm_pin, int(self._frequency))
            self._pwm_interface.start(0)  # Start with 0 duty cycle
            
            logger.info(f"Software PWM initialized on GPIO{self._pwm_pin}")
            
        except Exception as e:
            logger.error(f"Failed to initialize software PWM: {e}")
            self._pwm_interface = None
    
    def start(self) -> None:
        """Start continuous emission."""
        if self._emitting:
            logger.warning("Already emitting")
            return
        
        logger.info(f"Starting emission at {self._frequency}Hz")
        
        if self._use_hardware_pwm and self._pigpio_instance:
            # Hardware PWM: set frequency and duty cycle
            freq_hz = int(self._frequency)
            duty = int(self._amplitude * 500000)  # 0-1M range for pigpio
            self._pigpio_instance.hardware_PWM(self._pwm_pin, freq_hz, duty)
        
        elif self._pwm_interface:
            # Software PWM: change frequency and start
            self._pwm_interface.ChangeFrequency(int(self._frequency))
            self._pwm_interface.ChangeDutyCycle(int(self._amplitude * 50))
        
        else:
            logger.warning("No PWM interface available")
        
        self._emitting = True
        self._emission_start_time = time.time()
    
    def stop(self) -> None:
        """Stop emission."""
        if not self._emitting:
            return
        
        logger.info("Stopping emission")
        
        if self._use_hardware_pwm and self._pigpio_instance:
            self._pigpio_instance.hardware_PWM(self._pwm_pin, 0, 0)
        
        elif self._pwm_interface:
            self._pwm_interface.ChangeDutyCycle(0)
        
        self._emitting = False
        emission_time = time.time() - self._emission_start_time
        self._total_emission_time += emission_time
    
    def set_frequency(self, frequency: float) -> None:
        """
        Set emission frequency.
        
        Args:
            frequency: New frequency in Hz
        """
        self._frequency = frequency
        
        if self._emitting:
            # Update running emission
            if self._use_hardware_pwm and self._pigpio_instance:
                duty = int(self._amplitude * 500000)
                self._pigpio_instance.hardware_PWM(self._pwm_pin, int(frequency), duty)
            elif self._pwm_interface:
                self._pwm_interface.ChangeFrequency(int(frequency))
    
    def set_amplitude(self, amplitude: float) -> None:
        """
        Set emission amplitude.
        
        Args:
            amplitude: Amplitude 0-1
        """
        super().set_amplitude(amplitude)
        
        if self._emitting:
            # Update running emission
            if self._use_hardware_pwm and self._pigpio_instance:
                duty = int(self._amplitude * 500000)
                self._pigpio_instance.hardware_PWM(self._pwm_pin, int(self._frequency), duty)
            elif self._pwm_interface:
                self._pwm_interface.ChangeDutyCycle(int(self._amplitude * 50))
    
    def emit_burst(self, duration_ms: float, frequency: float | None = None) -> None:
        """
        Emit a single burst.
        
        Args:
            duration_ms: Burst duration in milliseconds
            frequency: Optional override frequency
        """
        if frequency is not None:
            orig_freq = self._frequency
            self.set_frequency(frequency)
        
        logger.debug(f"Emitting {duration_ms}ms burst at {self._frequency}Hz")
        
        self.start()
        time.sleep(duration_ms / 1000.0)
        self.stop()
        
        self._emission_count += 1
        
        if frequency is not None:
            self.set_frequency(orig_freq)
    
    def emit_chirp(
        self,
        start_freq: float,
        end_freq: float,
        duration_ms: float,
        amplitude: float = 1.0,
    ) -> None:
        """
        Emit frequency sweep (chirp).
        
        Note: Software PWM chirp uses stepped frequency changes.
        For smooth chirps, use external signal generator.
        
        Args:
            start_freq: Start frequency in Hz
            end_freq: End frequency in Hz
            duration_ms: Chirp duration in milliseconds
            amplitude: Emission amplitude 0-1
        """
        logger.info(
            f"Emitting chirp: {start_freq}-{end_freq}Hz over {duration_ms}ms"
        )
        
        # Number of frequency steps
        num_steps = max(10, int(duration_ms / 10))  # 10ms per step minimum
        step_duration = duration_ms / num_steps / 1000.0  # seconds
        
        frequencies = np.linspace(start_freq, end_freq, num_steps)
        
        self.set_amplitude(amplitude)
        
        for freq in frequencies:
            self.set_frequency(freq)
            if not self._emitting:
                self.start()
            time.sleep(step_duration)
        
        self.stop()
        self._emission_count += 1
    
    def _emit_signal(self, signal: NDArray[np.float64]) -> None:
        """
        Emit arbitrary signal.
        
        Note: PWM can only generate square waves. This method
        approximates the signal using PWM duty cycle modulation.
        
        Args:
            signal: Signal to emit (normalized -1 to 1)
        """
        # Convert signal to duty cycle changes
        # This is a simplified implementation
        samples = len(signal)
        duration_ms = samples / self._config.sample_rate * 1000
        
        # For now, just emit at average amplitude
        avg_amplitude = np.mean(np.abs(signal))
        self.emit_burst(duration_ms, amplitude=avg_amplitude)
    
    def get_stats(self) -> dict[str, float | int]:
        """Get emission statistics."""
        return {
            "emitting": float(self._emitting),
            "frequency": self._frequency,
            "amplitude": self._amplitude,
            "emission_count": self._emission_count,
            "total_emission_time_sec": self._total_emission_time,
            "hardware_pwm": float(self._use_hardware_pwm),
        }
    
    def close(self) -> None:
        """Release resources."""
        logger.info("Closing PWM transducer")
        self.stop()
        
        if self._burst_thread:
            self._burst_stop_event.set()
            self._burst_thread.join(timeout=1.0)
        
        if self._pwm_interface:
            self._pwm_interface.stop()
        
        if self._pigpio_instance:
            self._pigpio_instance.hardware_PWM(self._pwm_pin, 0, 0)
            self._pigpio_instance.stop()
        
        if RPI_GPIO_AVAILABLE:
            GPIO.cleanup(self._pwm_pin)
        
        super().close()


class MockPWMTransducer(PWMTransducer):
    """
    Mock PWM transducer for testing without hardware.
    
    Logs emission commands without actual hardware output.
    """
    
    def __init__(
        self,
        config: HardwareConfig,
        frequency: float = 40000.0,
        pwm_pin: int | None = None,
    ) -> None:
        """Initialize mock transducer."""
        # Skip parent init
        self._config = config
        self._frequency = frequency
        self._amplitude = 1.0
        self._emitting = False
        self._pwm_pin = pwm_pin or 18
        self._use_hardware_pwm = False
        self._emission_count = 0
        self._total_emission_time = 0.0
        self._emission_start_time: float = 0.0
        
        logger.info(f"MockPWMTransducer initialized: {frequency}Hz")
    
    def _initialize_pwm(self) -> None:
        """No hardware to initialize."""
        pass
    
    def start(self) -> None:
        """Mock start emission."""
        if not self._emitting:
            logger.info(f"[MOCK] Starting emission at {self._frequency}Hz")
            self._emitting = True
            self._emission_start_time = time.time()
    
    def stop(self) -> None:
        """Mock stop emission."""
        if self._emitting:
            logger.info("[MOCK] Stopping emission")
            self._emitting = False
            emission_time = time.time() - self._emission_start_time
            self._total_emission_time += emission_time
    
    def emit_burst(self, duration_ms: float, frequency: float | None = None) -> None:
        """Mock burst emission."""
        freq = frequency or self._frequency
        logger.info(f"[MOCK] Emitting {duration_ms}ms burst at {freq}Hz")
        self._emission_count += 1
        # Simulate timing
        time.sleep(duration_ms / 1000.0 * 0.1)  # 10x speedup
    
    def close(self) -> None:
        """Mock close."""
        logger.info("[MOCK] Closing transducer")
        self.stop()
