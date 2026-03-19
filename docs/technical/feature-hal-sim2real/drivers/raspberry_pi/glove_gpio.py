"""
GPIO Glove Interface for Raspberry Pi.

Interfaces with metamaterial glove sensors via GPIO:
- Flex sensors (analog via ADC)
- Pressure sensors (analog via ADC)
- IMU (I2C interface)
- Haptic feedback (PWM vibration motors)

Hardware Requirements:
- Raspberry Pi 4/5
- ADC (MCP3008 or similar) for analog sensors
- IMU (MPU6050 or similar) via I2C
- Vibration motors with drivers

Wiring:
- SPI for ADC:
  - GPIO 10 (Pin 19): MOSI
  - GPIO 9 (Pin 21): MISO
  - GPIO 11 (Pin 23): SCLK
  - GPIO 8 (Pin 24): CE0
- I2C for IMU:
  - GPIO 2 (Pin 3): SDA
  - GPIO 3 (Pin 5): SCL
- PWM for haptic:
  - GPIO 12 (Pin 32): PWM0
  - GPIO 13 (Pin 33): PWM1
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from ...hal.base import (
    AbstractGlove,
    GloveSensorData,
    HardwareConfig,
)


logger = logging.getLogger(__name__)

# Try to import hardware libraries
try:
    import board
    import busio
    import digitalio
    import pwmio
    from analogio import AnalogIn
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn as MCPAnalogIn
    CIRCUITPYTHON_AVAILABLE = True
except ImportError:
    logger.warning("CircuitPython libraries not available")
    CIRCUITPYTHON_AVAILABLE = False

try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    logger.warning("smbus2 not available")
    SMBUS_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    RPI_GPIO_AVAILABLE = True
except ImportError:
    logger.warning("RPi.GPIO not available")
    RPI_GPIO_AVAILABLE = False


# IMU constants (MPU6050)
MPU6050_ADDR = 0x68
MPU6050_REG_ACCEL_X = 0x3B
MPU6050_REG_GYRO_X = 0x43
MPU6050_REG_PWR_MGMT_1 = 0x6B

# ADC constants (MCP3008)
MCP3008_CHANNELS = 8


class GPIOGlove(AbstractGlove):
    """
    GPIO-based metamaterial glove interface for Raspberry Pi.
    
    Supports:
    - 5 flex sensors (finger bending)
    - 10 pressure sensors (contact detection)
    - 6-axis IMU (orientation tracking)
    - 2 haptic motors (tactile feedback)
    
    Example:
        >>> config = HardwareConfig()
        >>> glove = GPIOGlove(config)
        >>> glove.connect()
        >>> data = glove.read_sensors()
        >>> glove.set_vibration(0.5, "pulse")
        >>> glove.disconnect()
    """
    
    # Default pin assignments
    DEFAULT_PINS = {
        # SPI for ADC
        "spi_mosi": 10,
        "spi_miso": 9,
        "spi_sclk": 11,
        "spi_cs": 8,
        
        # I2C for IMU
        "i2c_sda": 2,
        "i2c_scl": 3,
        
        # PWM for haptic
        "haptic_left": 12,
        "haptic_right": 13,
    }
    
    # Sensor configuration
    NUM_FLEX_SENSORS = 5
    NUM_PRESSURE_SENSORS = 10
    
    # ADC channels
    FLEX_ADC_CHANNELS = [0, 1, 2, 3, 4]  # 5 flex sensors
    PRESSURE_ADC_CHANNELS = [5, 6, 7]  # 3 pressure on MCP3008
    
    # Calibration defaults
    FLEX_MIN_DEFAULT = 0.0
    FLEX_MAX_DEFAULT = 65535.0
    PRESSURE_OFFSET_DEFAULT = 0.0
    
    def __init__(
        self,
        config: HardwareConfig,
        pins: dict[str, int] | None = None,
        use_adc: bool = True,
        use_imu: bool = True,
    ) -> None:
        """
        Initialize GPIO glove interface.
        
        Args:
            config: Hardware configuration
            pins: Optional pin override
            use_adc: Enable ADC for analog sensors
            use_imu: Enable IMU
        """
        super().__init__(config)
        
        self._pins = pins or self.DEFAULT_PINS
        self._use_adc = use_adc and CIRCUITPYTHON_AVAILABLE
        self._use_imu = use_imu and SMBUS_AVAILABLE
        
        # Hardware interfaces
        self._spi: Any = None
        self._mcp: Any = None
        self._i2c: Any = None
        self._imu_bus: Any = None
        self._haptic_left: Any = None
        self._haptic_right: Any = None
        
        # Sensor calibration
        self._flex_min = np.full(self.NUM_FLEX_SENSORS, self.FLEX_MIN_DEFAULT)
        self._flex_max = np.full(self.NUM_FLEX_SENSORS, self.FLEX_MAX_DEFAULT)
        self._pressure_offset = np.full(self.NUM_PRESSURE_SENSORS, self.PRESSURE_OFFSET_DEFAULT)
        
        # Sensor cache
        self._last_sensor_data: GloveSensorData | None = None
        self._sensor_lock = threading.Lock()
        
        # Background polling
        self._poll_thread: threading.Thread | None = None
        self._poll_stop_event = threading.Event()
        self._poll_interval = 0.01  # 100Hz default
        
        logger.info(
            f"GPIOGlove initialized: flex={self.NUM_FLEX_SENSORS}, "
            f"pressure={self.NUM_PRESSURE_SENSORS}, imu={self._use_imu}"
        )
    
    def connect(self) -> None:
        """Connect to glove hardware."""
        if self._connected:
            logger.warning("Already connected")
            return
        
        logger.info("Connecting to glove hardware")
        
        try:
            if self._use_adc:
                self._initialize_adc()
            
            if self._use_imu:
                self._initialize_imu()
            
            self._initialize_haptic()
            
            self._connected = True
            logger.info("Glove connected successfully")
            
            # Start background polling
            self._start_polling()
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def _initialize_adc(self) -> None:
        """Initialize ADC for analog sensors."""
        try:
            if CIRCUITPYTHON_AVAILABLE:
                # Initialize SPI
                self._spi = busio.SPI(
                    clock=getattr(board, f"SCK"),
                    MOSI=getattr(board, f"MOSI"),
                    MISO=getattr(board, f"MISO"),
                )
                
                # Initialize chip select
                cs = digitalio.DigitalInOut(getattr(board, f"D{self._pins['spi_cs']}"))
                
                # Initialize MCP3008
                self._mcp = MCP.MCP3008(self._spi, cs)
                
                logger.info("ADC initialized (MCP3008)")
            else:
                logger.warning("ADC libraries not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize ADC: {e}")
            self._use_adc = False
    
    def _initialize_imu(self) -> None:
        """Initialize IMU via I2C."""
        try:
            if SMBUS_AVAILABLE:
                # Initialize I2C bus
                self._imu_bus = smbus2.SMBus(1)  # I2C bus 1 on RPi
                
                # Wake up MPU6050
                self._imu_bus.write_byte_data(MPU6050_ADDR, MPU6050_REG_PWR_MGMT_1, 0)
                
                # Verify connection
                who_am_i = self._imu_bus.read_byte_data(MPU6050_ADDR, 0x75)
                if who_am_i == 0x68:
                    logger.info("IMU initialized (MPU6050)")
                else:
                    logger.warning(f"Unexpected IMU ID: 0x{who_am_i:02X}")
            else:
                logger.warning("I2C libraries not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize IMU: {e}")
            self._use_imu = False
    
    def _initialize_haptic(self) -> None:
        """Initialize haptic feedback motors."""
        try:
            if RPI_GPIO_AVAILABLE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self._pins["haptic_left"], GPIO.OUT)
                GPIO.setup(self._pins["haptic_right"], GPIO.OUT)
                
                # Initialize PWM
                self._haptic_left = GPIO.PWM(self._pins["haptic_left"], 1000)
                self._haptic_right = GPIO.PWM(self._pins["haptic_right"], 1000)
                
                self._haptic_left.start(0)
                self._haptic_right.start(0)
                
                logger.info("Haptic motors initialized")
            else:
                logger.warning("GPIO libraries not available for haptic")
                
        except Exception as e:
            logger.error(f"Failed to initialize haptic: {e}")
    
    def _start_polling(self) -> None:
        """Start background sensor polling."""
        self._poll_stop_event.clear()
        self._poll_thread = threading.Thread(
            target=self._poll_sensors,
            name="GlovePoll",
            daemon=True,
        )
        self._poll_thread.start()
        logger.info("Sensor polling started")
    
    def _poll_sensors(self) -> None:
        """Background sensor polling thread."""
        while not self._poll_stop_event.is_set():
            try:
                data = self._read_raw_sensors()
                with self._sensor_lock:
                    self._last_sensor_data = GloveSensorData(
                        flex_values=data["flex"],
                        pressure_values=data["pressure"],
                        accelerometer=data["accel"],
                        gyroscope=data["gyro"],
                    )
                time.sleep(self._poll_interval)
            except Exception as e:
                logger.error(f"Sensor polling error: {e}")
                time.sleep(0.1)
    
    def disconnect(self) -> None:
        """Disconnect from glove hardware."""
        if not self._connected:
            return
        
        logger.info("Disconnecting from glove")
        
        # Stop polling
        self._poll_stop_event.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
        
        # Turn off haptic
        self.set_vibration(0.0)
        
        # Clean up hardware
        if self._haptic_left:
            self._haptic_left.stop()
        if self._haptic_right:
            self._haptic_right.stop()
        
        if RPI_GPIO_AVAILABLE:
            GPIO.cleanup()
        
        if self._imu_bus:
            self._imu_bus.close()
        
        self._connected = False
        logger.info("Glove disconnected")
    
    def _read_raw_sensors(self) -> dict[str, NDArray[np.float64]]:
        """Read raw sensor data from hardware."""
        flex = self._read_flex_sensors()
        pressure = self._read_pressure_sensors()
        accel, gyro = self._read_imu()
        
        return {
            "flex": flex,
            "pressure": pressure,
            "accel": accel,
            "gyro": gyro,
        }
    
    def _read_flex_sensors(self) -> NDArray[np.float64]:
        """Read flex sensor values."""
        values = np.zeros(self.NUM_FLEX_SENSORS)
        
        if not self._use_adc or not self._mcp:
            # Return simulated data
            return np.random.random(self.NUM_FLEX_SENSORS) * 0.5
        
        try:
            for i, channel in enumerate(self.FLEX_ADC_CHANNELS):
                if i < self.NUM_FLEX_SENSORS and channel < MCP3008_CHANNELS:
                    # Read from MCP3008
                    chan = MCPAnalogIn(self._mcp, channel)
                    raw_value = chan.value
                    # Normalize to 0-1
                    values[i] = np.clip(
                        (raw_value - self._flex_min[i]) / 
                        (self._flex_max[i] - self._flex_min[i] + 1e-6),
                        0, 1
                    )
        except Exception as e:
            logger.error(f"Flex sensor read error: {e}")
        
        return values
    
    def _read_pressure_sensors(self) -> NDArray[np.float64]:
        """Read pressure sensor values."""
        values = np.zeros(self.NUM_PRESSURE_SENSORS)
        
        if not self._use_adc or not self._mcp:
            # Return simulated data
            return np.random.random(self.NUM_PRESSURE_SENSORS) * 1000
        
        try:
            # Read from ADC channels
            for i, channel in enumerate(self.PRESSURE_ADC_CHANNELS):
                if i < len(self.PRESSURE_ADC_CHANNELS):
                    chan = MCPAnalogIn(self._mcp, channel)
                    raw_value = chan.value
                    # Convert to pressure (simplified)
                    values[i] = raw_value - self._pressure_offset[i]
        except Exception as e:
            logger.error(f"Pressure sensor read error: {e}")
        
        return values
    
    def _read_imu(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Read IMU data (accelerometer, gyroscope)."""
        accel = np.zeros(3)
        gyro = np.zeros(3)
        
        if not self._use_imu or not self._imu_bus:
            # Return simulated data
            return (
                np.random.randn(3) * 0.1 + np.array([0, 0, 9.8]),
                np.random.randn(3) * 0.01,
            )
        
        try:
            # Read accelerometer (6 bytes: x, y, z)
            accel_data = self._imu_bus.read_i2c_block_data(
                MPU6050_ADDR, MPU6050_REG_ACCEL_X, 6
            )
            
            # Convert to m/s^2 (MPU6050: 16384 LSB/g at +/- 2g)
            accel[0] = (accel_data[0] << 8 | accel_data[1]) / 16384.0 * 9.80665
            accel[1] = (accel_data[2] << 8 | accel_data[3]) / 16384.0 * 9.80665
            accel[2] = (accel_data[4] << 8 | accel_data[5]) / 16384.0 * 9.80665
            
            # Read gyroscope (6 bytes: x, y, z)
            gyro_data = self._imu_bus.read_i2c_block_data(
                MPU6050_ADDR, MPU6050_REG_GYRO_X, 6
            )
            
            # Convert to rad/s (MPU6050: 131 LSB/deg/s at +/- 250deg/s)
            gyro[0] = np.radians((gyro_data[0] << 8 | gyro_data[1]) / 131.0)
            gyro[1] = np.radians((gyro_data[2] << 8 | gyro_data[3]) / 131.0)
            gyro[2] = np.radians((gyro_data[4] << 8 | gyro_data[5]) / 131.0)
            
        except Exception as e:
            logger.error(f"IMU read error: {e}")
        
        return accel, gyro
    
    def read_sensors(self) -> GloveSensorData:
        """Read all sensor data."""
        with self._sensor_lock:
            if self._last_sensor_data is not None:
                return self._last_sensor_data
        
        # Fallback to direct read
        raw = self._read_raw_sensors()
        return GloveSensorData(
            flex_values=raw["flex"],
            pressure_values=raw["pressure"],
            accelerometer=raw["accel"],
            gyroscope=raw["gyro"],
        )
    
    def set_vibration(
        self,
        intensity: float,
        pattern: Literal["continuous", "pulse", "wave"] = "continuous",
    ) -> None:
        """
        Set haptic feedback intensity.
        
        Args:
            intensity: Vibration intensity 0-1
            pattern: Vibration pattern
        """
        intensity = np.clip(intensity, 0, 1)
        duty = int(intensity * 100)
        
        if pattern == "continuous":
            if self._haptic_left:
                self._haptic_left.ChangeDutyCycle(duty)
            if self._haptic_right:
                self._haptic_right.ChangeDutyCycle(duty)
        
        elif pattern == "pulse":
            # Pulse at 5Hz
            import threading
            def pulse():
                for _ in range(5):
                    if self._haptic_left:
                        self._haptic_left.ChangeDutyCycle(duty)
                    if self._haptic_right:
                        self._haptic_right.ChangeDutyCycle(duty)
                    time.sleep(0.1)
                    if self._haptic_left:
                        self._haptic_left.ChangeDutyCycle(0)
                    if self._haptic_right:
                        self._haptic_right.ChangeDutyCycle(0)
                    time.sleep(0.1)
            threading.Thread(target=pulse, daemon=True).start()
        
        elif pattern == "wave":
            # Alternating left/right
            import threading
            def wave():
                for _ in range(10):
                    if self._haptic_left:
                        self._haptic_left.ChangeDutyCycle(duty)
                    time.sleep(0.1)
                    if self._haptic_left:
                        self._haptic_left.ChangeDutyCycle(0)
                    if self._haptic_right:
                        self._haptic_right.ChangeDutyCycle(duty)
                    time.sleep(0.1)
                    if self._haptic_right:
                        self._haptic_right.ChangeDutyCycle(0)
            threading.Thread(target=wave, daemon=True).start()
        
        logger.debug(f"Haptic set: intensity={intensity}, pattern={pattern}")
    
    def calibrate(self) -> None:
        """Calibrate sensors."""
        logger.info("Starting glove calibration")
        
        # Calibrate flex sensors (min/max)
        logger.info("Flex calibration: relax fingers")
        time.sleep(2)
        flex_min_samples = []
        for _ in range(100):
            flex_min_samples.append(self._read_flex_sensors())
            time.sleep(0.01)
        self._flex_min = np.min(flex_min_samples, axis=0)
        
        logger.info("Flex calibration: bend fingers fully")
        time.sleep(2)
        flex_max_samples = []
        for _ in range(100):
            flex_max_samples.append(self._read_flex_sensors())
            time.sleep(0.01)
        self._flex_max = np.max(flex_max_samples, axis=0)
        
        # Calibrate pressure sensors (zero offset)
        logger.info("Pressure calibration: no contact")
        time.sleep(2)
        pressure_samples = []
        for _ in range(100):
            pressure_samples.append(self._read_pressure_sensors())
            time.sleep(0.01)
        self._pressure_offset = np.mean(pressure_samples, axis=0)
        
        logger.info("Calibration complete")
    
    def close(self) -> None:
        """Release resources."""
        self.disconnect()
        super().close()


class MockGPIOGlove(GPIOGlove):
    """
    Mock glove interface for testing without hardware.
    
    Generates synthetic sensor data for testing purposes.
    """
    
    def __init__(
        self,
        config: HardwareConfig,
        simulate_gestures: bool = True,
    ) -> None:
        """
        Initialize mock glove.
        
        Args:
            config: Hardware configuration
            simulate_gestures: Simulate realistic hand gestures
        """
        # Skip parent init
        self._config = config
        self._connected = False
        self._num_flex = 5
        self._num_pressure = 10
        self._has_imu = True
        self._simulate_gestures = simulate_gestures
        self._gesture_time = 0.0
        
        # Mock calibration
        self._flex_min = np.zeros(self.NUM_FLEX_SENSORS)
        self._flex_max = np.ones(self.NUM_FLEX_SENSORS)
        self._pressure_offset = np.zeros(self.NUM_PRESSURE_SENSORS)
        
        logger.info("MockGPIOGlove initialized")
    
    def connect(self) -> None:
        """Mock connect."""
        logger.info("[MOCK] Glove connected")
        self._connected = True
        self._gesture_time = time.time()
    
    def disconnect(self) -> None:
        """Mock disconnect."""
        logger.info("[MOCK] Glove disconnected")
        self._connected = False
    
    def _read_flex_sensors(self) -> NDArray[np.float64]:
        """Generate mock flex data."""
        if self._simulate_gestures:
            # Simulate opening/closing hand
            t = time.time() - self._gesture_time
            gesture = 0.5 + 0.4 * np.sin(2 * np.pi * 0.5 * t)  # 0.5Hz cycle
            
            # Each finger slightly different
            values = np.array([
                gesture,           # Thumb
                gesture * 0.9,     # Index
                gesture * 0.95,    # Middle
                gesture * 0.85,    # Ring
                gesture * 0.8,     # Pinky
            ])
            return np.clip(values, 0, 1)
        else:
            return np.random.random(self.NUM_FLEX_SENSORS)
    
    def _read_pressure_sensors(self) -> NDArray[np.float64]:
        """Generate mock pressure data."""
        if self._simulate_gestures:
            # Pressure when hand is closed (flex > 0.8)
            flex = self._read_flex_sensors()
            is_closed = np.mean(flex) > 0.7
            
            if is_closed:
                # Simulate gripping
                return np.random.random(self.NUM_PRESSURE_SENSORS) * 50000 + 10000
            else:
                return np.random.random(self.NUM_PRESSURE_SENSORS) * 100
        else:
            return np.random.random(self.NUM_PRESSURE_SENSORS) * 1000
    
    def _read_imu(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Generate mock IMU data."""
        # Simulate gravity + small movements
        accel = np.array([0.0, 0.0, 9.8]) + np.random.randn(3) * 0.1
        gyro = np.random.randn(3) * 0.05
        return accel, gyro
    
    def set_vibration(
        self,
        intensity: float,
        pattern: Literal["continuous", "pulse", "wave"] = "continuous",
    ) -> None:
        """Mock vibration."""
        logger.info(f"[MOCK] Vibration: intensity={intensity}, pattern={pattern}")
    
    def calibrate(self) -> None:
        """Mock calibration."""
        logger.info("[MOCK] Calibration complete")
