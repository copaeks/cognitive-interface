"""
Universal Shadow Engine - Core Module
=====================================

Core components for the plugin-based shadow tracking platform.
"""

from .data import (
    # Enumerations
    SensorType,
    ShadowQuality,
    ProcessingStage,
    
    # Data structures
    Vector3D,
    Timestamp,
    ShadowContour,
    RawSensorData,
    ShadowData,
    TrackingResult,
    
    # Configuration
    EngineConfig,
    PluginConfig,
    
    # Utilities
    compute_bounding_box,
    compute_centroid,
    estimate_surface_area,
)

from .engine import (
    # Exceptions
    PluginError,
    PluginNotFoundError,
    PluginRegistrationError,
    ProcessingError,
    
    # Base classes
    ShadowPlugin,
    ShadowProcessor,
    
    # Registry and Engine
    PluginRegistry,
    ShadowEngineCore,
    
    # Decorator
    shadow_plugin,
    
    # Pipeline
    ProcessingPipeline,
    TemporalSmoother,
    ConfidenceFilter,
)

__version__ = "2.0.0"
__all__ = [
    # Enums
    "SensorType",
    "ShadowQuality",
    "ProcessingStage",
    
    # Data structures
    "Vector3D",
    "Timestamp",
    "ShadowContour",
    "RawSensorData",
    "ShadowData",
    "TrackingResult",
    
    # Config
    "EngineConfig",
    "PluginConfig",
    
    # Exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginRegistrationError",
    "ProcessingError",
    
    # Base classes
    "ShadowPlugin",
    "ShadowProcessor",
    
    # Core
    "PluginRegistry",
    "ShadowEngineCore",
    "shadow_plugin",
    "ProcessingPipeline",
    "TemporalSmoother",
    "ConfidenceFilter",
    
    # Utilities
    "compute_bounding_box",
    "compute_centroid",
    "estimate_surface_area",
]
