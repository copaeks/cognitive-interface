"""
Universal Shadow Engine - Interfaces Module
===========================================

Interface implementations for various platforms and protocols.
"""

from .python_api import (
    ShadowTracker,
    ShadowTrackerConfig,
    MultiSensorTracker,
    AsyncShadowTracker,
    list_available_plugins,
    get_plugin_info,
    benchmark_tracker,
)

__version__ = "2.0.0"
__all__ = [
    "ShadowTracker",
    "ShadowTrackerConfig",
    "MultiSensorTracker",
    "AsyncShadowTracker",
    "list_available_plugins",
    "get_plugin_info",
    "benchmark_tracker",
]
