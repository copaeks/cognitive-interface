"""
Hardware Abstraction Layer (HAL) for Acoustic Sensor Arrays.

This module provides a unified interface for both simulation and real hardware,
enabling seamless sim-to-real transitions with a single flag.
"""

from .base import (
    MicrophoneArray,
    Transducer,
    GloveInterface,
    HardwareMode,
    SampleBuffer,
    CalibrationData,
    HardwareConfig,
)

from .factory import HardwareFactory, create_microphone_array, create_glove

__all__ = [
    "MicrophoneArray",
    "Transducer",
    "GloveInterface",
    "HardwareMode",
    "SampleBuffer",
    "CalibrationData",
    "HardwareConfig",
    "HardwareFactory",
    "create_microphone_array",
    "create_glove",
]
