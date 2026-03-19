#!/usr/bin/env python3
"""
Raspberry Pi 5 Setup Example for Acoustic Sensor Array.

This example demonstrates:
1. Hardware initialization for Raspberry Pi 5
2. Microphone array configuration
3. Ultrasonic emitter setup
4. Glove interface initialization
5. Basic data acquisition
6. Sim-to-real mode switching

Hardware Requirements:
- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- 4x I2S MEMS microphones (SPH0645 or INMP441)
- 1x Ultrasonic transducer (40kHz)
- 1x Metamaterial glove with sensors
- Appropriate wiring and power supply

Wiring Guide:
=============

I2S Microphones (4-channel):
---------------------------
Connect all microphones in parallel for BCLK and LRCLK,
separate DATA lines to GPIOs.

Mic 1 (Reference):
  - BCLK  -> GPIO 18 (Pin 12)
  - LRCLK -> GPIO 19 (Pin 35)
  - DATA  -> GPIO 20 (Pin 38)

Mic 2:
  - BCLK  -> GPIO 18 (shared)
  - LRCLK -> GPIO 19 (shared)
  - DATA  -> GPIO 21 (Pin 40)

Mic 3:
  - BCLK  -> GPIO 18 (shared)
  - LRCLK -> GPIO 19 (shared)
  - DATA  -> GPIO 16 (Pin 36)

Mic 4:
  - BCLK  -> GPIO 18 (shared)
  - LRCLK -> GPIO 19 (shared)
  - DATA  -> GPIO 26 (Pin 37)

Ultrasonic Emitter:
------------------
  - PWM   -> GPIO 12 (Pin 32) - Hardware PWM0
  - GND   -> Ground
  - VCC   -> 3.3V or 5V (with level shifter)

Glove Interface:
---------------
SPI (for ADC):
  - MOSI  -> GPIO 10 (Pin 19)
  - MISO  -> GPIO 9  (Pin 21)
  - SCLK  -> GPIO 11 (Pin 23)
  - CE0   -> GPIO 8  (Pin 24)

I2C (for IMU):
  - SDA   -> GPIO 2  (Pin 3)
  - SCL   -> GPIO 3  (Pin 5)

Haptic Motors:
  - Left  -> GPIO 13 (Pin 33) - PWM1
  - Right -> GPIO 12 (Pin 32) - PWM0 (shared with emitter if needed)

Installation:
=============

1. Enable I2C and SPI interfaces:
   sudo raspi-config
   # Interface Options -> I2C -> Enable
   # Interface Options -> SPI -> Enable

2. Install required packages:
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv
   sudo apt-get install -y libportaudio2 libatlas-base-dev

3. Install Python dependencies:
   pip install numpy scipy
   pip install RPi.GPIO smbus2 spidev
   pip install sounddevice
   # Optional: pigpio for hardware PWM
   pip install pigpio

4. Configure audio (for I2S):
   # Edit /boot/config.txt
   dtoverlay=i2s-mmap
   dtoverlay=generic-i2s

5. Reboot:
   sudo reboot

Usage:
======

    # Run in real mode on Raspberry Pi
    python raspberry_pi_setup.py --mode real

    # Run in simulation mode (for testing)
    python raspberry_pi_setup.py --mode sim

    # Record audio to file
    python raspberry_pi_setup.py --mode real --record audio.npy

    # Emit test tone
    python raspberry_pi_setup.py --mode real --emit-tone
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hal.factory import (
    HardwareFactory,
    create_microphone_array,
    create_transducer,
    create_glove,
    create_hardware_suite,
)
from hal.base import HardwareConfig, HardwareMode
from sim2real.bridge import Sim2RealBridge


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi 5 Acoustic Sensor Array Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic setup in simulation mode
  %(prog)s --mode sim

  # Setup with real hardware
  %(prog)s --mode real

  # Record audio
  %(prog)s --mode real --record audio.npy --duration 10

  # Emit test tone
  %(prog)s --mode real --emit-tone --frequency 40000 --duration 1000

  # Read glove sensors
  %(prog)s --mode real --read-glove
        """,
    )
    
    parser.add_argument(
        "--mode",
        choices=["sim", "real", "hybrid"],
        default="sim",
        help="Operation mode (default: sim)",
    )
    
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=48000,
        help="Audio sample rate (default: 48000)",
    )
    
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=1024,
        help="Audio buffer size (default: 1024)",
    )
    
    parser.add_argument(
        "--record",
        type=Path,
        metavar="FILE",
        help="Record audio to file",
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds (default: 5)",
    )
    
    parser.add_argument(
        "--emit-tone",
        action="store_true",
        help="Emit test tone",
    )
    
    parser.add_argument(
        "--frequency",
        type=float,
        default=40000,
        help="Tone frequency in Hz (default: 40000)",
    )
    
    parser.add_argument(
        "--tone-duration",
        type=float,
        default=1000,
        help="Tone duration in ms (default: 1000)",
    )
    
    parser.add_argument(
        "--read-glove",
        action="store_true",
        help="Read glove sensors",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    
    return parser.parse_args()


def check_platform() -> dict[str, bool]:
    """
    Check platform and available hardware.
    
    Returns:
        Dictionary of available features
    """
    import platform
    
    results = {
        "is_raspberry_pi": False,
        "rpi_gpio": False,
        "smbus": False,
        "spidev": False,
        "sounddevice": False,
        "pigpio": False,
    }
    
    # Check if running on Raspberry Pi
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read()
            results["is_raspberry_pi"] = "raspberry pi" in model.lower()
            if results["is_raspberry_pi"]:
                logger.info(f"Platform: {model.strip()}")
    except (FileNotFoundError, PermissionError):
        pass
    
    # Check libraries
    try:
        import RPi.GPIO
        results["rpi_gpio"] = True
        logger.info("RPi.GPIO: Available")
    except ImportError:
        logger.warning("RPi.GPIO: Not available")
    
    try:
        import smbus2
        results["smbus"] = True
        logger.info("smbus2: Available")
    except ImportError:
        logger.warning("smbus2: Not available")
    
    try:
        import spidev
        results["spidev"] = True
        logger.info("spidev: Available")
    except ImportError:
        logger.warning("spidev: Not available")
    
    try:
        import sounddevice
        results["sounddevice"] = True
        logger.info("sounddevice: Available")
    except ImportError:
        logger.warning("sounddevice: Not available")
    
    try:
        import pigpio
        results["pigpio"] = True
        logger.info("pigpio: Available")
    except ImportError:
        logger.warning("pigpio: Not available")
    
    return results


def setup_hardware(mode: str, config: HardwareConfig) -> dict:
    """
    Setup hardware components.
    
    Args:
        mode: Operation mode
        config: Hardware configuration
    
    Returns:
        Dictionary of hardware components
    """
    logger.info(f"Setting up hardware in {mode} mode")
    
    # Create hardware suite
    hw = create_hardware_suite(mode, config)
    
    logger.info("Hardware setup complete")
    logger.info(f"  Microphones: {hw['microphones'].num_microphones} channels")
    logger.info(f"  Transducer: {hw['transducer'].frequency}Hz")
    logger.info(f"  Glove: {hw['glove'].num_flex_sensors} flex sensors")
    
    return hw


def record_audio(
    microphones,
    duration: float,
    output_file: Path | None = None,
) -> np.ndarray:
    """
    Record audio from microphone array.
    
    Args:
        microphones: Microphone array instance
        duration: Recording duration in seconds
        output_file: Optional output file path
    
    Returns:
        Recorded audio data
    """
    logger.info(f"Recording audio for {duration} seconds...")
    
    # Start streaming
    microphones.start_stream()
    
    # Record for specified duration
    time.sleep(duration)
    
    # Read all available samples
    samples = microphones.read_available()
    
    # Stop streaming
    microphones.stop_stream()
    
    logger.info(f"Recorded {samples.n_samples} samples ({samples.duration:.3f}s)")
    
    # Save to file if requested
    if output_file:
        np.save(output_file, samples.data)
        logger.info(f"Audio saved to: {output_file}")
    
    return samples.data


def emit_test_tone(
    transducer,
    frequency: float,
    duration_ms: float,
) -> None:
    """
    Emit test tone from transducer.
    
    Args:
        transducer: Transducer instance
        frequency: Tone frequency in Hz
        duration_ms: Tone duration in milliseconds
    """
    logger.info(f"Emitting {duration_ms}ms tone at {frequency}Hz")
    
    # Set frequency
    transducer.set_frequency(frequency)
    
    # Emit burst
    transducer.emit_burst(duration_ms)
    
    logger.info("Tone emission complete")


def read_glove_sensors(glove) -> dict:
    """
    Read glove sensor data.
    
    Args:
        glove: Glove interface instance
    
    Returns:
        Dictionary of sensor readings
    """
    logger.info("Reading glove sensors...")
    
    # Connect if not already connected
    if not glove.is_connected:
        glove.connect()
    
    # Read sensors
    data = glove.read_sensors()
    
    # Format results
    results = {
        "flex": data.flex_values.tolist(),
        "pressure": data.pressure_values.tolist(),
        "accelerometer": data.accelerometer.tolist(),
        "gyroscope": data.gyroscope.tolist(),
    }
    
    logger.info("Glove sensor readings:")
    logger.info(f"  Flex: {results['flex']}")
    logger.info(f"  Pressure (avg): {np.mean(results['pressure']):.2f}")
    logger.info(f"  Accel magnitude: {np.linalg.norm(results['accelerometer']):.2f}")
    
    return results


def run_basic_demo(hw: dict, args: argparse.Namespace) -> None:
    """
    Run basic demonstration.
    
    Args:
        hw: Hardware components
        args: Command line arguments
    """
    print("\n" + "=" * 70)
    print("RASPBERRY PI 5 ACOUSTIC SENSOR ARRAY DEMO")
    print("=" * 70 + "\n")
    
    # Record audio if requested
    if args.record:
        audio = record_audio(
            hw["microphones"],
            args.duration,
            args.record,
        )
        print(f"\nRecorded audio shape: {audio.shape}")
        print(f"Audio RMS: {np.sqrt(np.mean(audio**2))}")
    
    # Emit test tone if requested
    if args.emit_tone:
        emit_test_tone(
            hw["transducer"],
            args.frequency,
            args.tone_duration,
        )
    
    # Read glove sensors if requested
    if args.read_glove:
        glove_data = read_glove_sensors(hw["glove"])
        print(f"\nGlove data: {glove_data}")
    
    # Default demo if no specific action requested
    if not any([args.record, args.emit_tone, args.read_glove]):
        print("Running default demo...\n")
        
        # Test microphone
        print("1. Testing microphones...")
        hw["microphones"].start_stream()
        time.sleep(0.5)
        samples = hw["microphones"].read_available()
        hw["microphones"].stop_stream()
        print(f"   Captured {samples.n_samples} samples")
        print(f"   RMS per channel: {np.sqrt(np.mean(samples.data**2, axis=0))}")
        
        # Test transducer
        print("\n2. Testing transducer...")
        emit_test_tone(hw["transducer"], 40000, 100)
        
        # Test glove
        print("\n3. Testing glove...")
        glove_data = read_glove_sensors(hw["glove"])
        print(f"   Flex sensors: {glove_data['flex']}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70 + "\n")


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Set verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check platform (only informative)
    if args.mode == "real":
        platform_info = check_platform()
        if not platform_info["is_raspberry_pi"]:
            logger.warning("Not running on Raspberry Pi - real mode may fail")
    
    # Create hardware configuration
    config = HardwareConfig(
        sample_rate=args.sample_rate,
        buffer_size=args.buffer_size,
        num_channels=4,
    )
    
    try:
        # Setup hardware
        hw = setup_hardware(args.mode, config)
        
        # Run demo
        run_basic_demo(hw, args)
        
        # Cleanup
        logger.info("Cleaning up...")
        hw["microphones"].close()
        hw["transducer"].close()
        hw["glove"].close()
        
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
