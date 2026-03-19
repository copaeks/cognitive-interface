"""
Python API for Universal Shadow Engine
======================================

High-level Python interface for shadow tracking applications.
Provides a simplified API for common use cases.

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Callable, Union, Type
from dataclasses import dataclass
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import (
    ShadowEngineCore, ShadowPlugin, PluginRegistry,
    shadow_plugin, ProcessingPipeline
)
from core.data import (
    ShadowData, ShadowContour, TrackingResult, RawSensorData,
    SensorType, ProcessingStage, EngineConfig, PluginConfig,
    Vector3D, Timestamp, ShadowQuality
)
from plugins import (
    AcousticPlugin, AcousticConfig,
    EMPlugin, EMConfig,
    THzPlugin, THzConfig,
    PhotoacousticPlugin, PhotoacousticConfig
)


# =============================================================================
# HIGH-LEVEL API CLASSES
# =============================================================================

@dataclass
class ShadowTrackerConfig:
    """Configuration for the ShadowTracker high-level API.
    
    Attributes:
        sensor_type: Primary sensor type to use
        max_latency_ms: Maximum allowed latency
        enable_smoothing: Enable temporal smoothing
        confidence_threshold: Minimum confidence for valid tracking
        debug_mode: Enable debug output
    """
    sensor_type: SensorType = SensorType.ACOUSTIC
    max_latency_ms: float = 10.0
    enable_smoothing: bool = True
    confidence_threshold: float = 0.5
    debug_mode: bool = False


class ShadowTracker:
    """High-level shadow tracking interface.
    
    This class provides a simplified API for shadow tracking
    applications, handling plugin management and data flow.
    
    Example:
        # Simple usage
        tracker = ShadowTracker.create_acoustic()
        tracker.initialize()
        
        # Process microphone signals
        signals = np.random.randn(4, 2048)
        result = tracker.track(signals)
        
        if result.tracked:
            print(f"Hand at: {result.position}")
    """
    
    def __init__(self, config: Optional[ShadowTrackerConfig] = None) -> None:
        """Initialize shadow tracker.
        
        Args:
            config: Tracker configuration. Uses defaults if None.
        """
        self.config = config or ShadowTrackerConfig()
        self._engine: Optional[ShadowEngineCore] = None
        self._plugin_name: Optional[str] = None
        self._initialized = False
        self._frame_count = 0
        
    @classmethod
    def create_acoustic(
        cls,
        sample_rate: int = 96000,
        n_mics: int = 4,
        **kwargs
    ) -> ShadowTracker:
        """Create an acoustic shadow tracker.
        
        Args:
            sample_rate: Sampling rate in Hz
            n_mics: Number of microphones
            **kwargs: Additional configuration options
            
        Returns:
            Configured ShadowTracker instance
        """
        config = ShadowTrackerConfig(
            sensor_type=SensorType.ACOUSTIC,
            **{k: v for k, v in kwargs.items() if k in ShadowTrackerConfig.__dataclass_fields__}
        )
        tracker = cls(config)
        
        # Create engine with acoustic plugin
        engine_config = EngineConfig(
            max_latency_ms=config.max_latency_ms,
            debug_mode=config.debug_mode
        )
        tracker._engine = ShadowEngineCore(engine_config)
        
        # Configure and load acoustic plugin
        acoustic_config = AcousticConfig(
            sample_rate=sample_rate,
            n_mics=n_mics,
            **{k: v for k, v in kwargs.items() if k in AcousticConfig.__dataclass_fields__}
        )
        tracker._engine.load_plugin("acoustic", acoustic_config)
        tracker._plugin_name = "acoustic"
        
        return tracker
    
    @classmethod
    def create_em(cls, **kwargs) -> ShadowTracker:
        """Create an electromagnetic shadow tracker."""
        config = ShadowTrackerConfig(
            sensor_type=SensorType.ELECTROMAGNETIC,
            **{k: v for k, v in kwargs.items() if hasattr(ShadowTrackerConfig, k)}
        )
        tracker = cls(config)
        
        engine_config = EngineConfig(
            max_latency_ms=config.max_latency_ms,
            debug_mode=config.debug_mode
        )
        tracker._engine = ShadowEngineCore(engine_config)
        
        em_config = EMConfig(
            **{k: v for k, v in kwargs.items() if hasattr(EMConfig, k)}
        )
        tracker._engine.load_plugin("em", em_config)
        tracker._plugin_name = "em"
        
        return tracker
    
    @classmethod
    def create_thz(cls, **kwargs) -> ShadowTracker:
        """Create a terahertz shadow tracker."""
        config = ShadowTrackerConfig(
            sensor_type=SensorType.TERAHERTZ,
            **{k: v for k, v in kwargs.items() if hasattr(ShadowTrackerConfig, k)}
        )
        tracker = cls(config)
        
        engine_config = EngineConfig(
            max_latency_ms=config.max_latency_ms,
            debug_mode=config.debug_mode
        )
        tracker._engine = ShadowEngineCore(engine_config)
        
        thz_config = THzConfig(
            **{k: v for k, v in kwargs.items() if hasattr(THzConfig, k)}
        )
        tracker._engine.load_plugin("thz", thz_config)
        tracker._plugin_name = "thz"
        
        return tracker
    
    @classmethod
    def create_photoacoustic(cls, **kwargs) -> ShadowTracker:
        """Create a photoacoustic shadow tracker."""
        config = ShadowTrackerConfig(
            sensor_type=SensorType.PHOTOACOUSTIC,
            **{k: v for k, v in kwargs.items() if hasattr(ShadowTrackerConfig, k)}
        )
        tracker = cls(config)
        
        engine_config = EngineConfig(
            max_latency_ms=config.max_latency_ms,
            debug_mode=config.debug_mode
        )
        tracker._engine = ShadowEngineCore(engine_config)
        
        pa_config = PhotoacousticConfig(
            **{k: v for k, v in kwargs.items() if hasattr(PhotoacousticConfig, k)}
        )
        tracker._engine.load_plugin("photoacoustic", pa_config)
        tracker._plugin_name = "photoacoustic"
        
        return tracker
    
    def initialize(self) -> bool:
        """Initialize the tracker and all plugins.
        
        Returns:
            True if initialization succeeded
        """
        if self._engine is None:
            raise RuntimeError("No plugin loaded. Use create_*() factory methods.")
        
        self._initialized = self._engine.initialize()
        return self._initialized
    
    def shutdown(self) -> None:
        """Shutdown the tracker and release resources."""
        if self._engine:
            self._engine.shutdown()
        self._initialized = False
    
    def track(self, raw_data: Union[np.ndarray, RawSensorData]) -> TrackingResult:
        """Track shadow from raw sensor data.
        
        Args:
            raw_data: Raw sensor data as numpy array or RawSensorData
            
        Returns:
            Tracking result with position and confidence
        """
        if not self._initialized:
            raise RuntimeError("Tracker not initialized. Call initialize() first.")
        
        # Convert numpy array to RawSensorData if needed
        if isinstance(raw_data, np.ndarray):
            raw_data = RawSensorData(
                sensor_type=self.config.sensor_type,
                raw_data=raw_data,
                sample_rate=96000  # Default, should be configurable
            )
        
        # Track through engine
        result = self._engine.track(raw_data)
        self._frame_count += 1
        
        # Apply confidence threshold
        if result.confidence < self.config.confidence_threshold:
            result.tracked = False
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics."""
        if self._engine is None:
            return {}
        return self._engine.get_stats()
    
    @property
    def is_initialized(self) -> bool:
        """Check if tracker is initialized."""
        return self._initialized
    
    @property
    def frame_count(self) -> int:
        """Get number of processed frames."""
        return self._frame_count


# =============================================================================
# MULTI-SENSOR FUSION
# =============================================================================

class MultiSensorTracker:
    """Multi-sensor shadow tracking with data fusion.
    
    Combines outputs from multiple sensor types for improved
    robustness and accuracy.
    
    Example:
        tracker = MultiSensorTracker()
        tracker.add_sensor("acoustic", ShadowTracker.create_acoustic())
        tracker.add_sensor("em", ShadowTracker.create_em())
        
        result = tracker.fuse_track(signals_dict)
    """
    
    def __init__(self, fusion_weights: Optional[Dict[str, float]] = None) -> None:
        """Initialize multi-sensor tracker.
        
        Args:
            fusion_weights: Weight for each sensor in fusion (should sum to 1)
        """
        self._trackers: Dict[str, ShadowTracker] = {}
        self._weights = fusion_weights or {}
        self._initialized = False
        
    def add_sensor(self, name: str, tracker: ShadowTracker, weight: float = 1.0) -> None:
        """Add a sensor tracker.
        
        Args:
            name: Sensor name
            tracker: ShadowTracker instance
            weight: Fusion weight for this sensor
        """
        self._trackers[name] = tracker
        self._weights[name] = weight
        
    def remove_sensor(self, name: str) -> bool:
        """Remove a sensor tracker.
        
        Args:
            name: Sensor name to remove
            
        Returns:
            True if sensor was found and removed
        """
        if name in self._trackers:
            del self._trackers[name]
            del self._weights[name]
            return True
        return False
    
    def initialize(self) -> bool:
        """Initialize all sensor trackers."""
        success = True
        for name, tracker in self._trackers.items():
            if not tracker.initialize():
                print(f"Warning: Failed to initialize {name}")
                success = False
        self._initialized = success
        return success
    
    def shutdown(self) -> None:
        """Shutdown all sensor trackers."""
        for tracker in self._trackers.values():
            tracker.shutdown()
        self._initialized = False
    
    def fuse_track(self, signals: Dict[str, np.ndarray]) -> TrackingResult:
        """Track and fuse results from all sensors.
        
        Args:
            signals: Dictionary mapping sensor names to raw data
            
        Returns:
            Fused tracking result
        """
        results: Dict[str, TrackingResult] = {}
        
        # Track with each sensor
        for name, tracker in self._trackers.items():
            if name in signals:
                results[name] = tracker.track(signals[name])
        
        # Fuse results (weighted average of positions)
        return self._fuse_results(results)
    
    def _fuse_results(self, results: Dict[str, TrackingResult]) -> TrackingResult:
        """Fuse multiple tracking results."""
        if not results:
            return TrackingResult(tracked=False, confidence=0.0)
        
        # Normalize weights
        total_weight = sum(
            self._weights.get(name, 1.0)
            for name in results.keys()
        )
        
        # Weighted position average
        fused_position = Vector3D()
        fused_confidence = 0.0
        total_latency = 0.0
        
        for name, result in results.items():
            if not result.tracked:
                continue
            
            weight = self._weights.get(name, 1.0) / total_weight
            
            fused_position = Vector3D(
                x=fused_position.x + weight * result.position.x,
                y=fused_position.y + weight * result.position.y,
                z=fused_position.z + weight * result.position.z
            )
            fused_confidence += weight * result.confidence
            total_latency = max(total_latency, result.latency_ms)
        
        return TrackingResult(
            tracked=fused_confidence > 0.3,
            position=fused_position,
            confidence=fused_confidence,
            timestamp=Timestamp(),
            latency_ms=total_latency
        )


# =============================================================================
# CALLBACK-BASED INTERFACE
# =============================================================================

class AsyncShadowTracker:
    """Asynchronous shadow tracker with callback support.
    
    Supports real-time tracking with callback-based result delivery.
    
    Example:
        def on_track(result: TrackingResult):
            print(f"Position: {result.position}")
        
        tracker = AsyncShadowTracker.create_acoustic()
        tracker.set_callback(on_track)
        tracker.start()
        
        # Feed data asynchronously
        tracker.feed(signals)
    """
    
    def __init__(self, tracker: ShadowTracker) -> None:
        """Initialize async tracker.
        
        Args:
            tracker: Underlying ShadowTracker instance
        """
        self._tracker = tracker
        self._callback: Optional[Callable[[TrackingResult], None]] = None
        self._running = False
        
    @classmethod
    def create_acoustic(cls, **kwargs) -> AsyncShadowTracker:
        """Create async acoustic tracker."""
        tracker = ShadowTracker.create_acoustic(**kwargs)
        return cls(tracker)
    
    def set_callback(self, callback: Callable[[TrackingResult], None]) -> None:
        """Set tracking result callback."""
        self._callback = callback
        
    def start(self) -> bool:
        """Start tracking."""
        if self._callback is None:
            raise RuntimeError("No callback set. Call set_callback() first.")
        
        self._running = self._tracker.initialize()
        return self._running
    
    def stop(self) -> None:
        """Stop tracking."""
        self._running = False
        self._tracker.shutdown()
    
    def feed(self, raw_data: Union[np.ndarray, RawSensorData]) -> None:
        """Feed raw data for processing.
        
        Args:
            raw_data: Raw sensor data
        """
        if not self._running:
            return
        
        result = self._tracker.track(raw_data)
        
        if self._callback:
            self._callback(result)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def list_available_plugins() -> List[str]:
    """List all available plugins in the registry.
    
    Returns:
        List of plugin names
    """
    registry = PluginRegistry()
    return registry.list_plugins()


def get_plugin_info(name: str) -> Dict[str, Any]:
    """Get information about a plugin.
    
    Args:
        name: Plugin name
        
    Returns:
        Plugin information dictionary
    """
    registry = PluginRegistry()
    return registry.get_metadata(name)


def benchmark_tracker(
    tracker: ShadowTracker,
    n_iterations: int = 1000,
    n_samples: int = 2048
) -> Dict[str, float]:
    """Benchmark a shadow tracker.
    
    Args:
        tracker: ShadowTracker instance to benchmark
        n_iterations: Number of iterations
        n_samples: Number of samples per frame
        
    Returns:
        Timing statistics
    """
    if not tracker.initialize():
        raise RuntimeError("Failed to initialize tracker")
    
    # Generate test data
    signals = np.random.randn(4, n_samples).astype(np.float32)
    
    # Warm-up
    for _ in range(10):
        tracker.track(signals)
    
    # Benchmark
    times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        tracker.track(signals)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    
    tracker.shutdown()
    
    times_arr = np.array(times)
    return {
        'mean_ms': float(np.mean(times_arr)),
        'std_ms': float(np.std(times_arr)),
        'min_ms': float(np.min(times_arr)),
        'max_ms': float(np.max(times_arr)),
        'p99_ms': float(np.percentile(times_arr, 99)),
        'throughput_fps': 1000.0 / float(np.mean(times_arr))
    }


# =============================================================================
# MAIN - API DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Universal Shadow Engine - Python API Demo")
    print("=" * 60)
    
    # List available plugins
    print("\n[1] Available Plugins:")
    plugins = list_available_plugins()
    for plugin in plugins:
        info = get_plugin_info(plugin)
        print(f"    - {plugin} v{info['version']} ({info['sensor_type'].name})")
    
    # Create and benchmark acoustic tracker
    print("\n[2] Creating Acoustic Tracker:")
    tracker = ShadowTracker.create_acoustic(
        sample_rate=96000,
        n_mics=4,
        max_latency_ms=10.0
    )
    
    print("    Initializing...")
    tracker.initialize()
    
    print("\n[3] Running Benchmark:")
    results = benchmark_tracker(tracker, n_iterations=1000)
    
    print(f"    Mean latency: {results['mean_ms']:.3f} ms")
    print(f"    P99 latency: {results['p99_ms']:.3f} ms")
    print(f"    Throughput: {results['throughput_fps']:.0f} fps")
    
    target = 10.0  # ms
    if results['p99_ms'] < target:
        print(f"    ✓ Target met: P99 < {target}ms")
    else:
        print(f"    ✗ Target missed: P99 = {results['p99_ms']:.2f}ms")
    
    # Test tracking
    print("\n[4] Testing Tracking:")
    signals = np.random.randn(4, 2048).astype(np.float32)
    result = tracker.track(signals)
    
    print(f"    Tracked: {result.tracked}")
    print(f"    Position: ({result.position.x:.3f}, {result.position.y:.3f}, {result.position.z:.3f})")
    print(f"    Confidence: {result.confidence:.3f}")
    print(f"    Latency: {result.latency_ms:.3f} ms")
    
    tracker.shutdown()
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)
