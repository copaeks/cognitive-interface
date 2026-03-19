"""
Universal Shadow Engine Core
============================

Plugin-based abstract core for the Shadow Principle platform.
Provides dynamic plugin registration, universal data processing,
and O(1) complexity shadow tracking.

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

from __future__ import annotations

import time
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar,
    get_type_hints, Protocol, runtime_checkable
)
from collections import OrderedDict
import numpy as np

from .data import (
    ShadowData, ShadowContour, TrackingResult, RawSensorData,
    SensorType, ProcessingStage, EngineConfig, PluginConfig,
    Timestamp, Vector3D, ShadowQuality
)


# =============================================================================
# TYPE VARIABLES
# =============================================================================

T = TypeVar('T')
P = TypeVar('P', bound='ShadowPlugin')


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not found."""
    pass


class PluginRegistrationError(PluginError):
    """Raised when plugin registration fails."""
    pass


class ProcessingError(Exception):
    """Raised when data processing fails."""
    pass


# =============================================================================
# ABSTRACT BASE CLASSES
# =============================================================================

class ShadowPlugin(ABC):
    """Abstract base class for all shadow tracking plugins.
    
    All sensor-specific implementations must inherit from this class
    and implement the required abstract methods.
    
    Example:
        @shadow_plugin(name="acoustic", version="2.0.0")
        class AcousticPlugin(ShadowPlugin):
            def process(self, data: ShadowData) -> ShadowData:
                # Implementation here
                pass
    """
    
    # Class attributes set by decorator
    _plugin_name: str = ""
    _plugin_version: str = "1.0.0"
    _plugin_sensor_type: SensorType = SensorType.UNKNOWN
    
    def __init__(self, config: Optional[PluginConfig] = None) -> None:
        """Initialize the plugin.
        
        Args:
            config: Plugin configuration. Uses defaults if None.
        """
        self.config = config or PluginConfig(name=self._plugin_name)
        self._initialized = False
        self._last_processing_time_ms = 0.0
        self._frame_count = 0
        
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self._plugin_name or self.__class__.__name__
    
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self._plugin_version
    
    @property
    def sensor_type(self) -> SensorType:
        """Get sensor type handled by this plugin."""
        return self._plugin_sensor_type
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin has been initialized."""
        return self._initialized
    
    @property
    def last_processing_time_ms(self) -> float:
        """Get last frame processing time in milliseconds."""
        return self._last_processing_time_ms
    
    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if initialization succeeded
            
        Raises:
            PluginError: If initialization fails
        """
        try:
            success = self._on_initialize()
            self._initialized = success
            return success
        except Exception as e:
            raise PluginError(f"Plugin {self.name} initialization failed: {e}") from e
    
    def shutdown(self) -> None:
        """Shutdown the plugin and release resources."""
        try:
            self._on_shutdown()
        finally:
            self._initialized = False
    
    def process(self, data: ShadowData) -> ShadowData:
        """Process shadow data through this plugin.
        
        This is the main entry point for data processing. It wraps
        the plugin-specific _process_impl method with timing and
        error handling.
        
        Args:
            data: Input shadow data
            
        Returns:
            Processed shadow data
            
        Raises:
            ProcessingError: If processing fails
        """
        if not self._initialized:
            raise ProcessingError(f"Plugin {self.name} not initialized")
        
        t0 = time.perf_counter()
        
        try:
            result = self._process_impl(data)
            self._frame_count += 1
        except Exception as e:
            raise ProcessingError(
                f"Plugin {self.name} processing failed: {e}"
            ) from e
        
        t1 = time.perf_counter()
        self._last_processing_time_ms = (t1 - t0) * 1000
        result.processing_time_ms += self._last_processing_time_ms
        
        return result
    
    @abstractmethod
    def _on_initialize(self) -> bool:
        """Plugin-specific initialization.
        
        Override this method to implement plugin initialization.
        
        Returns:
            True if initialization succeeded
        """
        pass
    
    @abstractmethod
    def _on_shutdown(self) -> None:
        """Plugin-specific shutdown.
        
        Override this method to release plugin resources.
        """
        pass
    
    @abstractmethod
    def _process_impl(self, data: ShadowData) -> ShadowData:
        """Plugin-specific processing implementation.
        
        Override this method to implement the actual processing logic.
        
        Args:
            data: Input shadow data
            
        Returns:
            Processed shadow data
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information.
        
        Returns:
            Dictionary with plugin metadata
        """
        return {
            'name': self.name,
            'version': self.version,
            'sensor_type': self.sensor_type.name,
            'initialized': self._initialized,
            'frame_count': self._frame_count,
            'last_processing_time_ms': self._last_processing_time_ms,
            'config': {
                'enabled': self.config.enabled,
                'priority': self.config.priority,
                'parameters': self.config.parameters
            }
        }


class ShadowProcessor(ABC):
    """Abstract base class for shadow data processors.
    
    Processors are lightweight transformation steps that can be
    chained together in a processing pipeline.
    """
    
    @abstractmethod
    def process(self, data: ShadowData) -> ShadowData:
        """Process shadow data.
        
        Args:
            data: Input shadow data
            
        Returns:
            Processed shadow data
        """
        pass
    
    def __call__(self, data: ShadowData) -> ShadowData:
        """Make processor callable."""
        return self.process(data)


# =============================================================================
# PLUGIN REGISTRY
# =============================================================================

class PluginRegistry:
    """Dynamic plugin registry with decorator-based registration.
    
    The registry maintains a mapping of plugin names to plugin classes,
    enabling runtime discovery and instantiation of plugins.
    
    Example:
        # Register a plugin
        @shadow_plugin(name="acoustic")
        class AcousticPlugin(ShadowPlugin):
            pass
        
        # Use the registry
        registry = PluginRegistry()
        plugin_class = registry.get("acoustic")
        plugin = plugin_class()
    """
    
    _instance: Optional[PluginRegistry] = None
    _plugins: Dict[str, Type[ShadowPlugin]] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls) -> PluginRegistry:
        """Singleton pattern for global registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(
        self,
        plugin_class: Type[P],
        name: Optional[str] = None,
        version: str = "1.0.0",
        sensor_type: SensorType = SensorType.UNKNOWN
    ) -> Type[P]:
        """Register a plugin class.
        
        Args:
            plugin_class: The plugin class to register
            name: Plugin name (defaults to class name)
            version: Plugin version string
            sensor_type: Sensor type handled by this plugin
            
        Returns:
            The registered plugin class (for decorator chaining)
            
        Raises:
            PluginRegistrationError: If registration fails
        """
        if not issubclass(plugin_class, ShadowPlugin):
            raise PluginRegistrationError(
                f"Class {plugin_class.__name__} must inherit from ShadowPlugin"
            )
        
        plugin_name = name or plugin_class.__name__
        
        if plugin_name in self._plugins:
            raise PluginRegistrationError(
                f"Plugin '{plugin_name}' already registered"
            )
        
        # Set class attributes for metadata
        plugin_class._plugin_name = plugin_name
        plugin_class._plugin_version = version
        plugin_class._plugin_sensor_type = sensor_type
        
        self._plugins[plugin_name] = plugin_class
        self._metadata[plugin_name] = {
            'version': version,
            'sensor_type': sensor_type,
            'class': plugin_class.__name__,
            'module': plugin_class.__module__,
            'registered_at': time.time()
        }
        
        return plugin_class
    
    def unregister(self, name: str) -> bool:
        """Unregister a plugin.
        
        Args:
            name: Plugin name to unregister
            
        Returns:
            True if plugin was found and removed
        """
        if name in self._plugins:
            del self._plugins[name]
            del self._metadata[name]
            return True
        return False
    
    def get(self, name: str) -> Type[ShadowPlugin]:
        """Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            The plugin class
            
        Raises:
            PluginNotFoundError: If plugin not found
        """
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        return self._plugins[name]
    
    def create(self, name: str, config: Optional[PluginConfig] = None) -> ShadowPlugin:
        """Create and return a plugin instance.
        
        Args:
            name: Plugin name
            config: Optional plugin configuration
            
        Returns:
            Instantiated plugin
        """
        plugin_class = self.get(name)
        return plugin_class(config)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names.
        
        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())
    
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin metadata dictionary
        """
        if name not in self._metadata:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        return self._metadata[name].copy()
    
    def get_by_sensor_type(self, sensor_type: SensorType) -> List[str]:
        """Get all plugins for a sensor type.
        
        Args:
            sensor_type: Sensor type to filter by
            
        Returns:
            List of plugin names
        """
        return [
            name for name, meta in self._metadata.items()
            if meta['sensor_type'] == sensor_type
        ]
    
    def clear(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._metadata.clear()
    
    @property
    def count(self) -> int:
        """Get number of registered plugins."""
        return len(self._plugins)


# =============================================================================
# DECORATOR FOR PLUGIN REGISTRATION
# =============================================================================

def shadow_plugin(
    name: Optional[str] = None,
    version: str = "1.0.0",
    sensor_type: SensorType = SensorType.UNKNOWN
) -> Callable[[Type[P]], Type[P]]:
    """Decorator for registering plugins with the PluginRegistry.
    
    This decorator registers a plugin class with the global registry
    and sets its metadata attributes.
    
    Args:
        name: Plugin name (defaults to class name)
        version: Plugin version string
        sensor_type: Sensor type handled by this plugin
        
    Returns:
        Decorator function that registers the plugin class
        
    Example:
        @shadow_plugin(name="acoustic", version="2.0.0", 
                      sensor_type=SensorType.ACOUSTIC)
        class AcousticPlugin(ShadowPlugin):
            def _process_impl(self, data: ShadowData) -> ShadowData:
                # Process acoustic data
                return data
    """
    def decorator(plugin_class: Type[P]) -> Type[P]:
        registry = PluginRegistry()
        registry.register(plugin_class, name, version, sensor_type)
        return plugin_class
    return decorator


# =============================================================================
# SHADOW ENGINE CORE
# =============================================================================

class ShadowEngineCore:
    """Core engine for the Universal Shadow Platform.
    
    The engine manages plugins, processes shadow data, and provides
    a unified interface for shadow tracking across all sensor types.
    
    Attributes:
        config: Engine configuration
        registry: Plugin registry instance
        active_plugins: Currently loaded plugins
        
    Example:
        engine = ShadowEngineCore()
        engine.load_plugin("acoustic")
        engine.initialize()
        
        result = engine.process(data)
    """
    
    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        """Initialize the shadow engine.
        
        Args:
            config: Engine configuration. Uses defaults if None.
        """
        self.config = config or EngineConfig()
        self.registry = PluginRegistry()
        self._active_plugins: Dict[str, ShadowPlugin] = {}
        self._initialized = False
        self._frame_counter = 0
        self._processing_times: List[float] = []
        
    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized
    
    @property
    def loaded_plugins(self) -> List[str]:
        """List names of loaded plugins."""
        return list(self._active_plugins.keys())
    
    def load_plugin(
        self,
        name: str,
        config: Optional[PluginConfig] = None
    ) -> ShadowPlugin:
        """Load and initialize a plugin.
        
        Args:
            name: Plugin name from registry
            config: Optional plugin configuration
            
        Returns:
            Loaded and initialized plugin instance
        """
        if name in self._active_plugins:
            return self._active_plugins[name]
        
        plugin = self.registry.create(name, config)
        self._active_plugins[name] = plugin
        
        return plugin
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.
        
        Args:
            name: Plugin name to unload
            
        Returns:
            True if plugin was found and unloaded
        """
        if name in self._active_plugins:
            self._active_plugins[name].shutdown()
            del self._active_plugins[name]
            return True
        return False
    
    def initialize(self) -> bool:
        """Initialize the engine and all loaded plugins.
        
        Returns:
            True if all plugins initialized successfully
        """
        if self._initialized:
            return True
        
        success = True
        for name, plugin in self._active_plugins.items():
            if not plugin.initialize():
                success = False
                if self.config.debug_mode:
                    print(f"Warning: Plugin {name} failed to initialize")
        
        self._initialized = success
        return success
    
    def shutdown(self) -> None:
        """Shutdown the engine and all plugins."""
        for plugin in self._active_plugins.values():
            plugin.shutdown()
        self._active_plugins.clear()
        self._initialized = False
    
    def process(self, data: ShadowData) -> ShadowData:
        """Process shadow data through active plugins.
        
        Data flows through plugins in priority order (highest first).
        Each plugin transforms the data and passes it to the next.
        
        Args:
            data: Input shadow data
            
        Returns:
            Processed shadow data
        """
        if not self._initialized:
            raise ProcessingError("Engine not initialized")
        
        self._frame_counter += 1
        data.frame_id = self._frame_counter
        
        t0 = time.perf_counter()
        
        # Sort plugins by priority (highest first)
        sorted_plugins = sorted(
            self._active_plugins.values(),
            key=lambda p: p.config.priority,
            reverse=True
        )
        
        # Process through each plugin
        result = data
        for plugin in sorted_plugins:
            if plugin.config.enabled:
                result = plugin.process(result)
        
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000
        self._processing_times.append(latency_ms)
        
        # Keep only recent timing data
        if len(self._processing_times) > 1000:
            self._processing_times = self._processing_times[-1000:]
        
        result.processing_time_ms = latency_ms
        
        return result
    
    def track(self, raw_data: RawSensorData) -> TrackingResult:
        """High-level tracking interface.
        
        Convenience method that wraps the full processing pipeline
        from raw sensor data to tracking result.
        
        Args:
            raw_data: Raw sensor data
            
        Returns:
            Tracking result with position and confidence
        """
        t_start = time.perf_counter()
        
        # Create shadow data container
        data = ShadowData(
            frame_id=self._frame_counter + 1,
            sensor_type=raw_data.sensor_type,
            raw_data=raw_data,
            stage=ProcessingStage.RAW
        )
        
        # Process through pipeline
        result = self.process(data)
        
        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000
        
        # Build tracking result
        if result.contour and result.contour.is_valid():
            return TrackingResult(
                tracked=True,
                position=result.contour.centroid,
                confidence=float(np.mean(result.contour.confidence)),
                contour=result.contour,
                timestamp=Timestamp(),
                latency_ms=latency_ms
            )
        
        return TrackingResult(
            tracked=False,
            confidence=0.0,
            timestamp=Timestamp(),
            latency_ms=latency_ms
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        stats = {
            'frame_count': self._frame_counter,
            'loaded_plugins': self.loaded_plugins,
            'initialized': self._initialized
        }
        
        if self._processing_times:
            times = np.array(self._processing_times)
            stats['latency_ms'] = {
                'mean': float(np.mean(times)),
                'std': float(np.std(times)),
                'min': float(np.min(times)),
                'max': float(np.max(times)),
                'p99': float(np.percentile(times, 99))
            }
        
        # Per-plugin stats
        stats['plugins'] = {
            name: plugin.get_info()
            for name, plugin in self._active_plugins.items()
        }
        
        return stats


# =============================================================================
# PROCESSING PIPELINE
# =============================================================================

class ProcessingPipeline:
    """Chainable processing pipeline for shadow data.
    
    Allows building custom processing chains by combining
    multiple processors in sequence.
    
    Example:
        pipeline = ProcessingPipeline()
        pipeline.add(Preprocessor())
        pipeline.add(Beamformer())
        pipeline.add(ShadowDetector())
        
        result = pipeline.process(data)
    """
    
    def __init__(self) -> None:
        """Initialize empty pipeline."""
        self._processors: List[ShadowProcessor] = []
        
    def add(self, processor: ShadowProcessor) -> ProcessingPipeline:
        """Add a processor to the pipeline.
        
        Args:
            processor: Processor to add
            
        Returns:
            Self for method chaining
        """
        self._processors.append(processor)
        return self
    
    def remove(self, processor: ShadowProcessor) -> bool:
        """Remove a processor from the pipeline.
        
        Args:
            processor: Processor to remove
            
        Returns:
            True if processor was found and removed
        """
        if processor in self._processors:
            self._processors.remove(processor)
            return True
        return False
    
    def clear(self) -> None:
        """Remove all processors."""
        self._processors.clear()
    
    def process(self, data: ShadowData) -> ShadowData:
        """Process data through the entire pipeline.
        
        Args:
            data: Input shadow data
            
        Returns:
            Processed shadow data
        """
        result = data
        for processor in self._processors:
            result = processor.process(result)
        return result
    
    def __call__(self, data: ShadowData) -> ShadowData:
        """Make pipeline callable."""
        return self.process(data)


# =============================================================================
# UTILITY PROCESSORS
# =============================================================================

class TemporalSmoother(ShadowProcessor):
    """Temporal smoothing processor using exponential moving average.
    
    Reduces jitter in contour positions by smoothing over time.
    """
    
    def __init__(self, alpha: float = 0.7, buffer_size: int = 5) -> None:
        """Initialize temporal smoother.
        
        Args:
            alpha: Smoothing factor (0-1, higher = more responsive)
            buffer_size: Number of frames to buffer
        """
        self.alpha = alpha
        self.buffer_size = buffer_size
        self._buffer: List[ShadowContour] = []
        
    def process(self, data: ShadowData) -> ShadowData:
        """Apply temporal smoothing to contour."""
        if data.contour is None:
            return data
        
        self._buffer.append(data.contour)
        if len(self._buffer) > self.buffer_size:
            self._buffer.pop(0)
        
        if len(self._buffer) < 2:
            return data
        
        # Exponential smoothing on centroid
        prev = self._buffer[-2].centroid
        curr = data.contour.centroid
        
        smoothed = Vector3D(
            x=self.alpha * curr.x + (1 - self.alpha) * prev.x,
            y=self.alpha * curr.y + (1 - self.alpha) * prev.y,
            z=self.alpha * curr.z + (1 - self.alpha) * prev.z
        )
        
        data.contour.centroid = smoothed
        return data


class ConfidenceFilter(ShadowProcessor):
    """Filter contours based on confidence threshold.
    
    Removes low-confidence detections from the output.
    """
    
    def __init__(self, threshold: float = 0.5) -> None:
        """Initialize confidence filter.
        
        Args:
            threshold: Minimum confidence value [0, 1]
        """
        self.threshold = threshold
        
    def process(self, data: ShadowData) -> ShadowData:
        """Filter by confidence."""
        if data.contour is None:
            return data
        
        mean_conf = float(np.mean(data.contour.confidence))
        if mean_conf < self.threshold:
            data.contour = None
            data.stage = ProcessingStage.DETECTED
        
        return data
