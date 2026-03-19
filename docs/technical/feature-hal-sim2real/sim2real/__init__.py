"""
Sim-to-Real Bridge for Acoustic Sensor Arrays.

Provides seamless switching between simulation and real hardware
with a single flag. Includes data validation, sanitization, and
graceful degradation.

Usage:
    >>> from sim2real.bridge import Sim2RealBridge
    >>> 
    >>> # Simulation mode
    >>> bridge = Sim2RealBridge(mode="sim")
    >>> 
    >>> # Real hardware mode
    >>> bridge = Sim2RealBridge(mode="real")
    >>> 
    >>> # Same API for both
    >>> mics = bridge.get_microphone_array()
    >>> data = mics.read(1024)
"""

from .bridge import (
    Sim2RealBridge,
    SimulatedMicrophoneArray,
    SimulatedTransducer,
    SimulatedGlove,
    DataValidator,
    SimRealMapper,
)

__all__ = [
    "Sim2RealBridge",
    "SimulatedMicrophoneArray",
    "SimulatedTransducer",
    "SimulatedGlove",
    "DataValidator",
    "SimRealMapper",
]
