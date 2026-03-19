"""
Hardware Factory for Creating Hardware Components.

Provides factory methods to create hardware components based on mode
(sim/real) and platform. Enables single-flag switching between simulation
and real hardware.
"""

from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING, Any

from .base import (
    AbstractGlove,
    AbstractMicrophoneArray,
    AbstractTransducer,
    HardwareConfig,
    HardwareMode,
    GloveInterface,
    MicrophoneArray,
    Transducer,
)

if TYPE_CHECKING:
    from ..drivers.raspberry_pi.microphone_i2s import I2SMicrophoneArray
    from ..drivers.raspberry_pi.emitter_pwm import PWMTransducer
    from ..drivers.raspberry_pi.glove_gpio import GPIOGlove


logger = logging.getLogger(__name__)


class HardwareFactory:
    """
    Factory for creating hardware components.
    
    Automatically detects platform and creates appropriate drivers.
    Falls back to simulation mode if real hardware is unavailable.
    
    Example:
        >>> factory = HardwareFactory(mode=HardwareMode.REAL)
        >>> mics = factory.create_microphone_array(config)
        >>> mics.start_stream()
    """
    
    def __init__(
        self,
        mode: HardwareMode = HardwareMode.SIMULATION,
        force_platform: str | None = None,
    ) -> None:
        """
        Initialize factory.
        
        Args:
            mode: Hardware operation mode
            force_platform: Override platform detection (for testing)
        """
        self._mode = mode
        self._platform = force_platform or self._detect_platform()
        self._components: dict[str, Any] = {}
        
        logger.info(f"HardwareFactory initialized: mode={mode.name}, platform={self._platform}")
    
    @property
    def mode(self) -> HardwareMode:
        """Current hardware mode."""
        return self._mode
    
    @property
    def platform(self) -> str:
        """Detected platform."""
        return self._platform
    
    def _detect_platform(self) -> str:
        """Detect current platform."""
        system = platform.system()
        machine = platform.machine()
        
        if system == "Linux":
            # Check for Raspberry Pi
            try:
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().lower()
                    if "raspberry pi" in model:
                        if "5" in model:
                            return "raspberry_pi_5"
                        elif "4" in model:
                            return "raspberry_pi_4"
                        else:
                            return "raspberry_pi"
            except (FileNotFoundError, PermissionError):
                pass
            
            # Check for other embedded boards
            if "arm" in machine.lower():
                return "arm_linux"
        
        elif system == "Darwin":
            return "macos"
        
        elif system == "Windows":
            return "windows"
        
        return "unknown"
    
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        return self._platform.startswith("raspberry_pi")
    
    def create_microphone_array(
        self,
        config: HardwareConfig | None = None,
        fallback_to_sim: bool = True,
    ) -> MicrophoneArray:
        """
        Create microphone array.
        
        Args:
            config: Hardware configuration
            fallback_to_sim: Fall back to simulation if real hardware fails
        
        Returns:
            MicrophoneArray implementation
        """
        config = config or HardwareConfig()
        
        if self._mode == HardwareMode.SIMULATION:
            return self._create_sim_microphone_array(config)
        
        try:
            if self.is_raspberry_pi():
                return self._create_rpi_microphone_array(config)
            else:
                logger.warning(f"No real microphone support for {self._platform}")
                if fallback_to_sim:
                    logger.info("Falling back to simulation")
                    return self._create_sim_microphone_array(config)
                raise RuntimeError(f"Real hardware not supported on {self._platform}")
        
        except Exception as e:
            logger.error(f"Failed to create real microphone array: {e}")
            if fallback_to_sim:
                logger.info("Falling back to simulation")
                return self._create_sim_microphone_array(config)
            raise
    
    def create_transducer(
        self,
        config: HardwareConfig | None = None,
        frequency: float = 40000.0,
        fallback_to_sim: bool = True,
    ) -> Transducer:
        """
        Create ultrasonic transducer/emitter.
        
        Args:
            config: Hardware configuration
            frequency: Operating frequency
            fallback_to_sim: Fall back to simulation if real hardware fails
        
        Returns:
            Transducer implementation
        """
        config = config or HardwareConfig()
        
        if self._mode == HardwareMode.SIMULATION:
            return self._create_sim_transducer(config, frequency)
        
        try:
            if self.is_raspberry_pi():
                return self._create_rpi_transducer(config, frequency)
            else:
                logger.warning(f"No real transducer support for {self._platform}")
                if fallback_to_sim:
                    logger.info("Falling back to simulation")
                    return self._create_sim_transducer(config, frequency)
                raise RuntimeError(f"Real hardware not supported on {self._platform}")
        
        except Exception as e:
            logger.error(f"Failed to create real transducer: {e}")
            if fallback_to_sim:
                logger.info("Falling back to simulation")
                return self._create_sim_transducer(config, frequency)
            raise
    
    def create_glove(
        self,
        config: HardwareConfig | None = None,
        fallback_to_sim: bool = True,
    ) -> GloveInterface:
        """
        Create glove interface.
        
        Args:
            config: Hardware configuration
            fallback_to_sim: Fall back to simulation if real hardware fails
        
        Returns:
            GloveInterface implementation
        """
        config = config or HardwareConfig()
        
        if self._mode == HardwareMode.SIMULATION:
            return self._create_sim_glove(config)
        
        try:
            if self.is_raspberry_pi():
                return self._create_rpi_glove(config)
            else:
                logger.warning(f"No real glove support for {self._platform}")
                if fallback_to_sim:
                    logger.info("Falling back to simulation")
                    return self._create_sim_glove(config)
                raise RuntimeError(f"Real hardware not supported on {self._platform}")
        
        except Exception as e:
            logger.error(f"Failed to create real glove: {e}")
            if fallback_to_sim:
                logger.info("Falling back to simulation")
                return self._create_sim_glove(config)
            raise
    
    def _create_sim_microphone_array(self, config: HardwareConfig) -> MicrophoneArray:
        """Create simulated microphone array."""
        from ..sim2real.bridge import SimulatedMicrophoneArray
        logger.info("Creating simulated microphone array")
        return SimulatedMicrophoneArray(config)
    
    def _create_sim_transducer(self, config: HardwareConfig, frequency: float) -> Transducer:
        """Create simulated transducer."""
        from ..sim2real.bridge import SimulatedTransducer
        logger.info("Creating simulated transducer")
        return SimulatedTransducer(config, frequency)
    
    def _create_sim_glove(self, config: HardwareConfig) -> GloveInterface:
        """Create simulated glove."""
        from ..sim2real.bridge import SimulatedGlove
        logger.info("Creating simulated glove")
        return SimulatedGlove(config)
    
    def _create_rpi_microphone_array(self, config: HardwareConfig) -> MicrophoneArray:
        """Create Raspberry Pi I2S microphone array."""
        from ..drivers.raspberry_pi.microphone_i2s import I2SMicrophoneArray
        logger.info("Creating Raspberry Pi I2S microphone array")
        return I2SMicrophoneArray(config)
    
    def _create_rpi_transducer(self, config: HardwareConfig, frequency: float) -> Transducer:
        """Create Raspberry Pi PWM transducer."""
        from ..drivers.raspberry_pi.emitter_pwm import PWMTransducer
        logger.info("Creating Raspberry Pi PWM transducer")
        return PWMTransducer(config, frequency)
    
    def _create_rpi_glove(self, config: HardwareConfig) -> GloveInterface:
        """Create Raspberry Pi GPIO glove interface."""
        from ..drivers.raspberry_pi.glove_gpio import GPIOGlove
        logger.info("Creating Raspberry Pi GPIO glove interface")
        return GPIOGlove(config)
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a custom component."""
        self._components[name] = component
    
    def get_component(self, name: str) -> Any:
        """Get registered component."""
        return self._components.get(name)


# Convenience functions for quick hardware creation

def create_microphone_array(
    mode: HardwareMode | str = HardwareMode.SIMULATION,
    config: HardwareConfig | None = None,
    fallback_to_sim: bool = True,
) -> MicrophoneArray:
    """
    Quick factory function for microphone arrays.
    
    Args:
        mode: Hardware mode (can be string: "sim", "real", "hybrid")
        config: Hardware configuration
        fallback_to_sim: Fall back to simulation on failure
    
    Returns:
        MicrophoneArray implementation
    
    Example:
        >>> # Simulation mode
        >>> mics = create_microphone_array("sim")
        >>> 
        >>> # Real hardware mode
        >>> mics = create_microphone_array("real")
        >>> mics.start_stream()
    """
    if isinstance(mode, str):
        mode = HardwareMode[mode.upper()]
    
    factory = HardwareFactory(mode=mode)
    return factory.create_microphone_array(config, fallback_to_sim)


def create_transducer(
    mode: HardwareMode | str = HardwareMode.SIMULATION,
    config: HardwareConfig | None = None,
    frequency: float = 40000.0,
    fallback_to_sim: bool = True,
) -> Transducer:
    """
    Quick factory function for transducers.
    
    Args:
        mode: Hardware mode
        config: Hardware configuration
        frequency: Operating frequency
        fallback_to_sim: Fall back to simulation on failure
    
    Returns:
        Transducer implementation
    """
    if isinstance(mode, str):
        mode = HardwareMode[mode.upper()]
    
    factory = HardwareFactory(mode=mode)
    return factory.create_transducer(config, frequency, fallback_to_sim)


def create_glove(
    mode: HardwareMode | str = HardwareMode.SIMULATION,
    config: HardwareConfig | None = None,
    fallback_to_sim: bool = True,
) -> GloveInterface:
    """
    Quick factory function for gloves.
    
    Args:
        mode: Hardware mode
        config: Hardware configuration
        fallback_to_sim: Fall back to simulation on failure
    
    Returns:
        GloveInterface implementation
    """
    if isinstance(mode, str):
        mode_map = {
            "sim": HardwareMode.SIMULATION,
            "simulation": HardwareMode.SIMULATION,
            "real": HardwareMode.REAL,
            "hybrid": HardwareMode.HYBRID,
        }
        mode = mode_map.get(mode.lower(), HardwareMode.SIMULATION)
    
    factory = HardwareFactory(mode=mode)
    return factory.create_glove(config, fallback_to_sim)


def create_hardware_suite(
    mode: HardwareMode | str = HardwareMode.SIMULATION,
    config: HardwareConfig | None = None,
    fallback_to_sim: bool = True,
) -> dict[str, Any]:
    """
    Create complete hardware suite.
    
    Args:
        mode: Hardware mode
        config: Hardware configuration
        fallback_to_sim: Fall back to simulation on failure
    
    Returns:
        Dictionary with 'microphones', 'transducer', 'glove' keys
    
    Example:
        >>> hw = create_hardware_suite("real")
        >>> hw['microphones'].start_stream()
        >>> hw['transducer'].emit_burst(100)
        >>> data = hw['glove'].read_sensors()
    """
    if isinstance(mode, str):
        mode_map = {
            "sim": HardwareMode.SIMULATION,
            "simulation": HardwareMode.SIMULATION,
            "real": HardwareMode.REAL,
            "hybrid": HardwareMode.HYBRID,
        }
        mode = mode_map.get(mode.lower(), HardwareMode.SIMULATION)
    
    factory = HardwareFactory(mode=mode)
    config = config or HardwareConfig()
    
    return {
        "microphones": factory.create_microphone_array(config, fallback_to_sim),
        "transducer": factory.create_transducer(config, fallback_to_sim=fallback_to_sim),
        "glove": factory.create_glove(config, fallback_to_sim),
    }
