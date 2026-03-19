# Hardware Abstraction Layer (HAL) for Acoustic Sensor Arrays

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade Hardware Abstraction Layer with Sim-to-Real Bridge for acoustic sensor arrays. Provides a unified interface for both simulation and real hardware, enabling seamless development and deployment on Raspberry Pi 5.

## Features

- **Unified Interface**: Same API for simulation and real hardware
- **Single-Flag Switching**: `mode="sim"` or `mode="real"` 
- **Raspberry Pi 5 Support**: Full I2S, PWM, and GPIO drivers
- **Automatic Calibration**: Gain, phase, time-of-flight, and position calibration
- **Uncertainty Quantification**: GUM-compliant uncertainty estimation
- **Data Validation**: Automatic validation and sanitization
- **Graceful Degradation**: Falls back to simulation on hardware failure
- **Real-Time Performance**: Optimized for low-latency audio processing

## Quick Start

```python
from hal.factory import create_microphone_array, create_glove

# Simulation mode (for development)
mics = create_microphone_array("sim")
mics.start_stream()
data = mics.read(1024)
mics.stop_stream()

# Real hardware mode (for deployment)
mics = create_microphone_array("real")
mics.start_stream()
data = mics.read(1024)  # Same API!
mics.stop_stream()
```

## Installation

### Requirements

- Python 3.12+
- NumPy, SciPy
- Raspberry Pi: RPi.GPIO, smbus2, spidev (optional)

### Basic Installation

```bash
pip install numpy scipy
```

### Raspberry Pi Installation

```bash
# Enable interfaces
sudo raspi-config
# Interface Options -> I2C -> Enable
# Interface Options -> SPI -> Enable

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip libportaudio2 libatlas-base-dev

# Install Python packages
pip install numpy scipy RPi.GPIO smbus2 spidev sounddevice

# Optional: Hardware PWM support
pip install pigpio
```

## Project Structure

```
feature-hal-sim2real/
├── hal/
│   ├── __init__.py          # HAL package exports
│   ├── base.py              # Abstract interfaces (MicrophoneArray, Transducer, Glove)
│   └── factory.py           # Hardware factory for device creation
├── drivers/
│   └── raspberry_pi/
│       ├── __init__.py
│       ├── microphone_i2s.py    # I2S MEMS microphone driver
│       ├── emitter_pwm.py       # PWM ultrasonic emitter driver
│       └── glove_gpio.py        # GPIO glove interface
├── calibration/
│   ├── __init__.py
│   ├── auto_calibrate.py        # Automatic calibration procedures
│   └── uncertainty.py           # Uncertainty quantification (GUM)
├── sim2real/
│   ├── __init__.py
│   └── bridge.py                # Sim-to-real bridge implementation
├── tests/
│   ├── test_hal.py              # HAL interface tests
│   ├── test_calibration.py      # Calibration tests
│   └── test_sim2real.py         # Sim-to-real bridge tests
├── scripts/
│   └── calibrate_array.py       # Calibration script
├── examples/
│   └── raspberry_pi_setup.py    # Raspberry Pi setup example
└── README.md
```

## Hardware Abstraction Layer

### Core Interfaces

#### MicrophoneArray

```python
from hal.base import MicrophoneArray, HardwareConfig

class MyMicrophoneArray(MicrophoneArray):
    @property
    def num_microphones(self) -> int: ...
    
    @property
    def sample_rate(self) -> int: ...
    
    def start_stream(self) -> None: ...
    def stop_stream(self) -> None: ...
    def read(self, num_samples: int | None = None) -> SampleBuffer: ...
```

#### Transducer

```python
from hal.base import Transducer

class MyTransducer(Transducer):
    @property
    def frequency(self) -> float: ...
    
    def emit_burst(self, duration_ms: float) -> None: ...
    def emit_chirp(self, start_freq: float, end_freq: float, duration_ms: float) -> None: ...
```

#### GloveInterface

```python
from hal.base import GloveInterface

class MyGlove(GloveInterface):
    def read_sensors(self) -> GloveSensorData: ...
    def set_vibration(self, intensity: float, pattern: str) -> None: ...
```

### Hardware Factory

The factory pattern enables single-flag switching:

```python
from hal.factory import HardwareFactory, HardwareMode

# Create factory
factory = HardwareFactory(mode=HardwareMode.REAL)

# Create components
mics = factory.create_microphone_array(config)
transducer = factory.create_transducer(config, frequency=40000)
glove = factory.create_glove(config)

# Or use convenience functions
from hal.factory import create_microphone_array, create_glove, create_transducer

mics = create_microphone_array("real")  # Same API!
```

## Sim-to-Real Bridge

### Basic Usage

```python
from sim2real.bridge import Sim2RealBridge

# Create bridge
bridge = Sim2RealBridge(mode="sim")  # or "real"

# Get components (same API for both modes)
mics = bridge.get_microphone_array()
transducer = bridge.get_transducer(frequency=40000)
glove = bridge.get_glove()

# Use components
mics.start_stream()
transducer.emit_burst(100)
data = mics.read(1024)
mics.stop_stream()
```

### Data Validation

```python
# Validate data automatically
validation = bridge.validate_data(
    audio_data=samples.data,
    glove_data=sensor_data,
)

print(f"Audio valid: {validation['audio']['valid']}")
print(f"Issues: {validation['audio']['issues']}")
```

### Mode Switching

```python
# Development (simulation)
bridge = Sim2RealBridge(mode="sim")

# Testing (hybrid - some real, some simulated)
bridge = Sim2RealBridge(mode="hybrid")

# Production (real hardware)
bridge = Sim2RealBridge(mode="real")
```

## Raspberry Pi 5 Drivers

### I2S Microphone Array

Supports 4-channel MEMS microphones via I2S interface.

```python
from drivers.raspberry_pi import I2SMicrophoneArray
from hal.base import HardwareConfig

config = HardwareConfig(
    sample_rate=48000,
    num_channels=4,
    buffer_size=1024,
)

mics = I2SMicrophoneArray(config)
mics.start_stream()
data = mics.read(1024)
mics.stop_stream()
```

**Wiring:**
- BCLK: GPIO 18 (Pin 12)
- LRCLK: GPIO 19 (Pin 35)
- DATA: GPIO 20, 21, 16, 26 (Pins 38, 40, 36, 37)

### PWM Ultrasonic Emitter

Controls 40kHz ultrasonic transducers with hardware PWM.

```python
from drivers.raspberry_pi import PWMTransducer

transducer = PWMTransducer(config, frequency=40000, pwm_pin=12)
transducer.emit_burst(100)  # 100ms burst
transducer.emit_chirp(30000, 50000, 50)  # Frequency sweep
```

**Wiring:**
- PWM: GPIO 12 (Pin 32) - Hardware PWM0
- Connect to transducer driver circuit

### GPIO Glove Interface

Interfaces with metamaterial glove sensors.

```python
from drivers.raspberry_pi import GPIOGlove

glove = GPIOGlove(config)
glove.connect()
data = glove.read_sensors()
glove.set_vibration(0.5, "pulse")
glove.disconnect()
```

**Wiring:**
- SPI (ADC): GPIO 10, 9, 11, 8
- I2C (IMU): GPIO 2, 3
- PWM (Haptic): GPIO 12, 13

## Calibration

### Automatic Calibration

```python
from calibration.auto_calibrate import ArrayCalibrator
from hal.factory import create_microphone_array, create_transducer

# Create hardware
mics = create_microphone_array("real")
transducer = create_transducer("real")

# Create calibrator
calibrator = ArrayCalibrator(mics, transducer)

# Run calibration
result = calibrator.calibrate()

# Save calibration
result.calibration.save("calibration.json")

print(f"Quality: {result.quality_score:.3f}")
```

### Calibration Procedures

1. **ToneCalibration**: Calibrates gain and phase using known frequencies
2. **ImpulseCalibration**: Calibrates time-of-flight using impulses
3. **PositionCalibration**: Calibrates microphone geometry

### Using Calibration Script

```bash
# Full calibration
python scripts/calibrate_array.py --mode real --output calibration.json

# Validate existing calibration
python scripts/calibrate_array.py --validate calibration.json

# Generate report
python scripts/calibrate_array.py --input calibration.json --report report.txt
```

## Uncertainty Quantification

### GUM-Compliant Uncertainty

```python
from calibration.uncertainty import UncertaintyEstimator, CalibrationValidator

# Estimate uncertainty
estimator = UncertaintyEstimator()

# Gain uncertainty
uncertainty = estimator.estimate_gain_uncertainty(measurements)

# Create uncertainty budget
budgets = estimator.create_calibration_budget(calibration)

print(f"Gain uncertainty: {budgets['gain'].combined_uncertainty()}")
print(f"Expanded (k=2): {budgets['gain'].expanded_uncertainty(2.0)}")

# Validate calibration
validator = CalibrationValidator()
results = validator.full_validation(calibration)

print(f"Valid: {results['valid']}")
print(f"Recommendations: {results['recommendations']}")
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_hal.py -v
pytest tests/test_calibration.py -v
pytest tests/test_sim2real.py -v

# Run with coverage
pytest tests/ --cov=hal --cov=sim2real --cov=calibration
```

### Hardware-in-the-Loop Testing

```python
# Mock hardware for testing
from drivers.raspberry_pi.microphone_i2s import MockI2SMicrophoneArray
from drivers.raspberry_pi.emitter_pwm import MockPWMTransducer
from drivers.raspberry_pi.glove_gpio import MockGPIOGlove

# Use mocks in tests
mics = MockI2SMicrophoneArray(config)
transducer = MockPWMTransducer(config)
glove = MockGPIOGlove(config)
```

## Raspberry Pi Setup Example

```bash
# Run the setup example
python examples/raspberry_pi_setup.py --mode real

# Record audio
python examples/raspberry_pi_setup.py --mode real --record audio.npy --duration 10

# Emit test tone
python examples/raspberry_pi_setup.py --mode real --emit-tone --frequency 40000

# Read glove sensors
python examples/raspberry_pi_setup.py --mode real --read-glove
```

## Sim-to-Real Migration Guide

### Step 1: Develop in Simulation

```python
# Development - pure simulation
from sim2real.bridge import Sim2RealBridge

bridge = Sim2RealBridge(mode="sim")
mics = bridge.get_microphone_array()

# Add simulated signal sources
mics.add_tone_source(frequency=1000, amplitude=0.5)

# Test algorithms
mics.start_stream()
data = mics.read(1024)
# ... process data ...
mics.stop_stream()
```

### Step 2: Test with Hybrid Mode

```python
# Hybrid - some real, some simulated
bridge = Sim2RealBridge(mode="hybrid")

# Real microphones with simulated glove
mics = bridge.get_microphone_array()  # Real
glove = bridge.get_glove()  # Simulated (fallback)
```

### Step 3: Deploy on Real Hardware

```python
# Production - real hardware
bridge = Sim2RealBridge(mode="real")

# Same API as simulation!
mics = bridge.get_microphone_array()
mics.start_stream()
data = mics.read(1024)
# ... same processing code ...
mics.stop_stream()
```

## Configuration

### HardwareConfig

```python
from hal.base import HardwareConfig

config = HardwareConfig(
    sample_rate=48000,      # Audio sample rate
    buffer_size=1024,       # Audio buffer size
    num_channels=4,         # Number of microphones
    bit_depth=24,           # ADC bit depth
    frame_duration_ms=20,   # Processing frame duration
    max_latency_ms=5,       # Maximum acceptable latency
    calibration_file=None,  # Path to calibration file
    auto_calibrate=True,    # Enable auto-calibration
    i2s_bus=0,              # I2S bus number
    pwm_pin=18,             # PWM pin number
    gpio_chip=0,            # GPIO chip number
)
```

### CalibrationData

```python
from hal.base import CalibrationData

calibration = CalibrationData(
    gain_calibration=np.array([1.0, 1.02, 0.98, 1.01]),
    time_offset=np.array([0.0, 1e-6, -1e-6, 0.0]),
    phase_calibration=np.array([0.0, 0.1, -0.1, 0.0]),
    microphone_positions=np.array([
        [0.015, 0.0, 0.0],
        [0.0, 0.015, 0.0],
        [-0.015, 0.0, 0.0],
        [0.0, -0.015, 0.0],
    ]),
    quality_score=0.95,
)

# Save/load
calibration.save("calibration.json")
loaded = CalibrationData.load("calibration.json")
```

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'RPi'`
- **Solution**: Install RPi.GPIO: `pip install RPi.GPIO`
- **Note**: This is expected on non-Raspberry Pi systems

**Issue**: `No suitable I2S device found`
- **Solution**: Enable I2S interface in `raspi-config`
- **Check**: Verify wiring and device tree overlay

**Issue**: Audio has glitches or dropouts
- **Solution**: Increase buffer size or use hardware PWM
- **Check**: CPU load with `top` or `htop`

**Issue**: Calibration fails with low quality score
- **Solution**: Check microphone connections, reduce noise
- **Try**: Multiple calibration runs and average results

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
python script.py -v
```

## Performance Optimization

### Raspberry Pi 5 Optimization

1. **Use Hardware PWM**: Better timing accuracy
2. **Increase Buffer Size**: Reduce CPU load
3. **Disable Unnecessary Services**: Free up CPU
4. **Use Real-Time Kernel**: For critical applications

```bash
# Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Set to performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## API Reference

See inline documentation in source files:
- `hal/base.py`: Core interfaces
- `hal/factory.py`: Hardware factory
- `drivers/raspberry_pi/`: Platform drivers
- `calibration/`: Calibration procedures
- `sim2real/bridge.py`: Sim-to-real bridge

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- GUM (Guide to the Expression of Uncertainty in Measurement)
- Raspberry Pi Foundation
- Python Audio Community
