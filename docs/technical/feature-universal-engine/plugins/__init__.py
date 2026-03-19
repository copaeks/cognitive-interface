"""
Universal Shadow Engine - Plugins Module
========================================

Plugin implementations for various sensing modalities.
"""

from .acoustic import AcousticPlugin, AcousticConfig
from .em import EMPlugin, EMConfig
from .thz import THzPlugin, THzConfig
from .photoacoustic import PhotoacousticPlugin, PhotoacousticConfig

__version__ = "2.0.0"
__all__ = [
    # Acoustic
    "AcousticPlugin",
    "AcousticConfig",
    # EM
    "EMPlugin",
    "EMConfig",
    # THz
    "THzPlugin",
    "THzConfig",
    # Photoacoustic
    "PhotoacousticPlugin",
    "PhotoacousticConfig",
]
