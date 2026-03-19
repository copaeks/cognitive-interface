"""
Universal Shadow Engine - Example Usage
=======================================

Demonstrates how to use the Universal Shadow Engine for
shadow tracking applications.

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

import numpy as np
import time

from core.engine import ShadowEngineCore, PluginRegistry, shadow_plugin
from core.data import (
    ShadowData, RawSensorData, SensorType, EngineConfig,
    PluginConfig, Vector3D, Timestamp
)
from interfaces.python_api import (
    ShadowTracker, MultiSensorTracker, AsyncShadowTracker,
    list_available_plugins, get_plugin_info, benchmark_tracker
)
from plugins.acoustic import AcousticPlugin, AcousticConfig


# =============================================================================
# EXAMPLE 1: BASIC USAGE WITH HIGH-LEVEL API
# =============================================================================

def example_basic_tracking():
    """Basic shadow tracking with the high-level API."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Shadow Tracking")
    print("=" * 60)
    
    # Create an acoustic shadow tracker
    tracker = ShadowTracker.create_acoustic(
        sample_rate=96000,
        n_mics=4,
        max_latency_ms=10.0
    )
    
    # Initialize the tracker
    print("\n[1] Initializing tracker...")
    tracker.initialize()
    
    # Generate sample microphone signals (4 mics, 2048 samples)
    print("[2] Generating sample signals...")
    signals = np.random.randn(4, 2048).astype(np.float32)
    
    # Track shadow
    print("[3] Tracking shadow...")
    result = tracker.track(signals)
    
    # Display results
    print("\n[4] Results:")
    print(f"    Tracked: {result.tracked}")
    print(f"    Position: ({result.position.x:.3f}, {result.position.y:.3f}, {result.position.z:.3f}) m")
    print(f"    Confidence: {result.confidence:.3f}")
    print(f"    Latency: {result.latency_ms:.3f} ms")
    
    # Shutdown
    tracker.shutdown()
    print("\n✓ Example complete")


# =============================================================================
# EXAMPLE 2: LOW-LEVEL API WITH CUSTOM PLUGIN
# =============================================================================

def example_custom_plugin():
    """Create and use a custom plugin."""
    print("\n" + "=" * 60)
    print("Example 2: Custom Plugin Creation")
    print("=" * 60)
    
    # Define a custom plugin (in < 50 lines!)
    @shadow_plugin(name="custom", version="1.0.0", sensor_type=SensorType.UNKNOWN)
    class CustomPlugin(ShadowPlugin):
        """Custom plugin that adds a constant offset to contours."""
        
        def _on_initialize(self) -> bool:
            print("    Custom plugin initialized!")
            return True
        
        def _on_shutdown(self) -> None:
            print("    Custom plugin shutdown!")
        
        def _process_impl(self, data: ShadowData) -> ShadowData:
            if data.contour:
                # Add offset to centroid
                data.contour.centroid = Vector3D(
                    data.contour.centroid.x + 0.01,
                    data.contour.centroid.y + 0.01,
                    data.contour.centroid.z
                )
            return data
    
    # Create engine and load plugins
    print("\n[1] Creating engine...")
    engine = ShadowEngineCore()
    
    print("[2] Loading plugins...")
    engine.load_plugin("acoustic")
    engine.load_plugin("custom", PluginConfig(name="custom", priority=5))
    
    print("[3] Initializing engine...")
    engine.initialize()
    
    # Create sample data
    print("[4] Processing sample data...")
    signals = np.random.randn(4, 2048).astype(np.float32)
    raw_data = RawSensorData(
        sensor_type=SensorType.ACOUSTIC,
        raw_data=signals,
        sample_rate=96000
    )
    
    # Track
    result = engine.track(raw_data)
    print(f"\n[5] Result: tracked={result.tracked}, confidence={result.confidence:.3f}")
    
    engine.shutdown()
    print("\n✓ Example complete")


# =============================================================================
# EXAMPLE 3: MULTI-SENSOR FUSION
# =============================================================================

def example_multi_sensor():
    """Multi-sensor tracking with data fusion."""
    print("\n" + "=" * 60)
    print("Example 3: Multi-Sensor Fusion")
    print("=" * 60)
    
    # Create multi-sensor tracker
    print("\n[1] Creating multi-sensor tracker...")
    multi_tracker = MultiSensorTracker()
    
    # Add sensors
    print("[2] Adding sensors...")
    acoustic_tracker = ShadowTracker.create_acoustic()
    em_tracker = ShadowTracker.create_em()
    
    multi_tracker.add_sensor("acoustic", acoustic_tracker, weight=0.6)
    multi_tracker.add_sensor("em", em_tracker, weight=0.4)
    
    # Initialize
    print("[3] Initializing...")
    multi_tracker.initialize()
    
    # Generate sample data for each sensor
    print("[4] Generating sample data...")
    signals = {
        "acoustic": np.random.randn(4, 2048).astype(np.float32),
        "em": np.random.randn(8, 100).astype(np.float32)
    }
    
    # Fuse track
    print("[5] Fusing tracks...")
    result = multi_tracker.fuse_track(signals)
    
    print(f"\n[6] Fused Result:")
    print(f"    Tracked: {result.tracked}")
    print(f"    Position: ({result.position.x:.3f}, {result.position.y:.3f}) m")
    print(f"    Confidence: {result.confidence:.3f}")
    
    multi_tracker.shutdown()
    print("\n✓ Example complete")


# =============================================================================
# EXAMPLE 4: ASYNCHRONOUS TRACKING
# =============================================================================

def example_async_tracking():
    """Asynchronous tracking with callbacks."""
    print("\n" + "=" * 60)
    print("Example 4: Asynchronous Tracking")
    print("=" * 60)
    
    # Create async tracker
    print("\n[1] Creating async tracker...")
    async_tracker = AsyncShadowTracker.create_acoustic()
    
    # Set callback
    results_received = [0]
    
    def on_result(result):
        results_received[0] += 1
        if results_received[0] <= 3:
            print(f"    [{results_received[0]}] Tracked: {result.tracked}, "
                  f"Confidence: {result.confidence:.3f}")
    
    async_tracker.set_callback(on_result)
    
    # Start tracking
    print("[2] Starting tracker...")
    async_tracker.start()
    
    # Feed data
    print("[3] Feeding data (10 frames)...")
    for i in range(10):
        signals = np.random.randn(4, 2048).astype(np.float32)
        async_tracker.feed(signals)
        time.sleep(0.001)  # Small delay
    
    # Stop
    print("[4] Stopping tracker...")
    async_tracker.stop()
    
    print(f"\n✓ Received {results_received[0]} results")


# =============================================================================
# EXAMPLE 5: BENCHMARKING
# =============================================================================

def example_benchmarking():
    """Benchmark plugin performance."""
    print("\n" + "=" * 60)
    print("Example 5: Performance Benchmarking")
    print("=" * 60)
    
    # Create tracker
    print("\n[1] Creating tracker...")
    tracker = ShadowTracker.create_acoustic()
    
    # Run benchmark
    print("[2] Running benchmark (1000 iterations)...")
    results = benchmark_tracker(tracker, n_iterations=1000)
    
    # Display results
    print("\n[3] Results:")
    print(f"    Mean latency: {results['mean_ms']:.3f} ms")
    print(f"    Std dev: {results['std_ms']:.3f} ms")
    print(f"    Min latency: {results['min_ms']:.3f} ms")
    print(f"    Max latency: {results['max_ms']:.3f} ms")
    print(f"    P99 latency: {results['p99_ms']:.3f} ms")
    print(f"    Throughput: {results['throughput_fps']:.0f} fps")
    
    # Check target
    target = 10.0  # ms
    if results['p99_ms'] < target:
        print(f"\n    ✓ Target met: P99 < {target}ms")
    else:
        print(f"\n    ✗ Target missed: P99 = {results['p99_ms']:.2f}ms")


# =============================================================================
# EXAMPLE 6: PLUGIN REGISTRY
# =============================================================================

def example_plugin_registry():
    """Explore the plugin registry."""
    print("\n" + "=" * 60)
    print("Example 6: Plugin Registry")
    print("=" * 60)
    
    # List available plugins
    print("\n[1] Available plugins:")
    plugins = list_available_plugins()
    for plugin in plugins:
        info = get_plugin_info(plugin)
        print(f"    - {plugin} v{info['version']} ({info['sensor_type'].name})")
    
    # Get detailed info
    print("\n[2] Acoustic plugin details:")
    info = get_plugin_info("acoustic")
    for key, value in info.items():
        print(f"    {key}: {value}")


# =============================================================================
# EXAMPLE 7: PROCESSING PIPELINE
# =============================================================================

def example_processing_pipeline():
    """Custom processing pipeline."""
    print("\n" + "=" * 60)
    print("Example 7: Custom Processing Pipeline")
    print("=" * 60)
    
    from core.engine import ProcessingPipeline, TemporalSmoother, ConfidenceFilter
    
    # Create pipeline
    print("\n[1] Creating pipeline...")
    pipeline = ProcessingPipeline()
    
    # Add processors
    print("[2] Adding processors...")
    pipeline.add(TemporalSmoother(alpha=0.7))
    pipeline.add(ConfidenceFilter(threshold=0.5))
    
    # Create sample data
    print("[3] Creating sample data...")
    from core.data import ShadowContour
    points = np.array([[0.1, 0, 0], [0, 0.1, 0], [-0.1, 0, 0]])
    data = ShadowData(
        contour=ShadowContour(
            points=points,
            confidence=np.array([0.9, 0.8, 0.9]),
            centroid=Vector3D(0.05, 0.05, 0),
            area=0.01
        )
    )
    
    # Process
    print("[4] Processing through pipeline...")
    result = pipeline.process(data)
    
    print(f"\n[5] Result: contour valid = {result.contour.is_valid() if result.contour else False}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all examples."""
    print("=" * 60)
    print("Universal Shadow Engine - Example Usage")
    print("=" * 60)
    
    examples = [
        ("Basic Tracking", example_basic_tracking),
        ("Custom Plugin", example_custom_plugin),
        ("Multi-Sensor Fusion", example_multi_sensor),
        ("Async Tracking", example_async_tracking),
        ("Benchmarking", example_benchmarking),
        ("Plugin Registry", example_plugin_registry),
        ("Processing Pipeline", example_processing_pipeline),
    ]
    
    print(f"\nRunning {len(examples)} examples...")
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example {i} ({name}) failed: {e}")
    
    print("\n" + "=" * 60)
    print("All examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
