"""
Acoustic Shadow Plugin
======================

PAST (Passive Acoustic Shadow Tracking) plugin for the Universal Shadow Engine.
"""

from .plugin import (
    AcousticPlugin,
    AcousticConfig,
    create_default_acoustic_plugin,
    benchmark_acoustic_plugin,
    SPEED_OF_SOUND,
    AIR_DENSITY,
)

__version__ = "2.0.0"
__all__ = [
    "AcousticPlugin",
    "AcousticConfig",
    "create_default_acoustic_plugin",
    "benchmark_acoustic_plugin",
    "SPEED_OF_SOUND",
    "AIR_DENSITY",
]
