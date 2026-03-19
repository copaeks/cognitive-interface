"""
Universal Shadow Engine
=======================

Plugin-based abstract core for the Shadow Principle platform.

Provides:
- Universal shadow data structures
- Dynamic plugin registration
- O(1) complexity shadow tracking
- Multi-sensor fusion capabilities

Example:
    >>> from interfaces.python_api import ShadowTracker
    >>> tracker = ShadowTracker.create_acoustic()
    >>> tracker.initialize()
    >>> result = tracker.track(signals)
    >>> print(f"Position: {result.position}")

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__author__ = "Cognitive AR Empire 2035 Technical Team"
__license__ = "MIT"

# Import core components for convenience
from core.data import (
    SensorType,
    ShadowQuality,
    ProcessingStage,
    Vector3D,
    Timestamp,
    ShadowContour,
    RawSensorData,
    ShadowData,
    TrackingResult,
    EngineConfig,
    PluginConfig,
)

from core.engine import (
    ShadowPlugin,
    ShadowProcessor,
    ShadowEngineCore,
    PluginRegistry,
    shadow_plugin,
    ProcessingPipeline,
    PluginError,
    PluginNotFoundError,
    PluginRegistrationError,
    ProcessingError,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Data structures
    "SensorType",
    "ShadowQuality",
    "ProcessingStage",
    "Vector3D",
    "Timestamp",
    "ShadowContour",
    "RawSensorData",
    "ShadowData",
    "TrackingResult",
    "EngineConfig",
    "PluginConfig",
    
    # Core engine
    "ShadowPlugin",
    "ShadowProcessor",
    "ShadowEngineCore",
    "PluginRegistry",
    "shadow_plugin",
    "ProcessingPipeline",
    
    # Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginRegistrationError",
    "ProcessingError",
]
