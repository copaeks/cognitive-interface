"""
Photoacoustic Shadow Plugin
===========================

Stub implementation for photoacoustic shadow tracking.
"""

from .plugin import (
    PhotoacousticPlugin,
    PhotoacousticConfig,
    create_default_photoacoustic_plugin
)

__version__ = "0.1.0"
__all__ = [
    "PhotoacousticPlugin",
    "PhotoacousticConfig",
    "create_default_photoacoustic_plugin"
]
