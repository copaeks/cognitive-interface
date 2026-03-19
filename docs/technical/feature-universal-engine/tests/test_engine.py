"""
Unit Tests for Universal Shadow Engine Core
============================================

Comprehensive tests for the core engine, plugin registry, and data structures.

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

import pytest
import numpy as np
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import (
    ShadowPlugin, ShadowProcessor, ShadowEngineCore,
    PluginRegistry, shadow_plugin, ProcessingPipeline,
    PluginError, PluginNotFoundError, PluginRegistrationError,
    ProcessingError, TemporalSmoother, ConfidenceFilter
)
from core.data import (
    ShadowData, ShadowContour, RawSensorData, TrackingResult,
    SensorType, ProcessingStage, EngineConfig, PluginConfig,
    Vector3D, Timestamp, ShadowQuality,
    compute_bounding_box, compute_centroid, estimate_surface_area
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def registry():
    """Create a fresh plugin registry for each test."""
    registry = PluginRegistry()
    registry.clear()
    return registry


@pytest.fixture
def sample_contour():
    """Create a sample shadow contour."""
    points = np.array([
        [0.1, 0.0, 0.0],
        [0.0, 0.1, 0.0],
        [-0.1, 0.0, 0.0],
        [0.0, -0.1, 0.0]
    ], dtype=np.float32)
    
    return ShadowContour(
        points=points,
        confidence=np.array([0.9, 0.8, 0.9, 0.8], dtype=np.float32),
        centroid=Vector3D(0, 0, 0),
        area=0.02,
        normal=Vector3D(0, 0, 1),
        timestamp=Timestamp(),
        quality=ShadowQuality.GOOD
    )


@pytest.fixture
def sample_raw_data():
    """Create sample raw sensor data."""
    return RawSensorData(
        sensor_type=SensorType.ACOUSTIC,
        raw_data=np.random.randn(4, 512).astype(np.float32),
        sample_rate=96000,
        timestamp=Timestamp()
    )


@pytest.fixture
def sample_shadow_data(sample_raw_data):
    """Create sample shadow data."""
    return ShadowData(
        frame_id=1,
        sensor_type=SensorType.ACOUSTIC,
        raw_data=sample_raw_data,
        stage=ProcessingStage.RAW
    )


# =============================================================================
# TEST: DATA STRUCTURES
# =============================================================================

class TestVector3D:
    """Test Vector3D data structure."""
    
    def test_default_creation(self):
        """Test default Vector3D creation."""
        v = Vector3D()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0
    
    def test_custom_creation(self):
        """Test Vector3D with custom values."""
        v = Vector3D(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_to_array(self):
        """Test conversion to numpy array."""
        v = Vector3D(1.0, 2.0, 3.0)
        arr = v.to_array()
        assert np.allclose(arr, [1.0, 2.0, 3.0])
    
    def test_from_array(self):
        """Test creation from numpy array."""
        arr = np.array([1.0, 2.0, 3.0])
        v = Vector3D.from_array(arr)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_distance_to(self):
        """Test distance calculation."""
        v1 = Vector3D(0, 0, 0)
        v2 = Vector3D(3, 4, 0)
        assert v1.distance_to(v2) == 5.0


class TestShadowContour:
    """Test ShadowContour data structure."""
    
    def test_default_creation(self):
        """Test default ShadowContour creation."""
        contour = ShadowContour()
        assert len(contour.points) == 0
        assert contour.area == 0.0
    
    def test_valid_contour(self, sample_contour):
        """Test valid contour detection."""
        assert sample_contour.is_valid()
    
    def test_invalid_contour(self):
        """Test invalid contour detection."""
        contour = ShadowContour(points=np.zeros((2, 3)))
        assert not contour.is_valid()
    
    def test_quality_computation(self, sample_contour):
        """Test quality computation from confidence."""
        assert sample_contour.quality == ShadowQuality.GOOD
    
    def test_to_dict(self, sample_contour):
        """Test dictionary conversion."""
        d = sample_contour.to_dict()
        assert 'points' in d
        assert 'confidence' in d
        assert 'centroid' in d


class TestShadowData:
    """Test ShadowData data structure."""
    
    def test_creation(self, sample_shadow_data):
        """Test ShadowData creation."""
        assert sample_shadow_data.frame_id == 1
        assert sample_shadow_data.sensor_type == SensorType.ACOUSTIC
    
    def test_copy(self, sample_shadow_data):
        """Test ShadowData copying."""
        copy = sample_shadow_data.copy()
        assert copy.frame_id == sample_shadow_data.frame_id
        assert copy.sensor_type == sample_shadow_data.sensor_type


# =============================================================================
# TEST: PLUGIN REGISTRY
# =============================================================================

class TestPluginRegistry:
    """Test PluginRegistry functionality."""
    
    def test_singleton(self, registry):
        """Test registry singleton pattern."""
        registry2 = PluginRegistry()
        assert registry is registry2
    
    def test_register_plugin(self, registry):
        """Test plugin registration."""
        @shadow_plugin(name="test_plugin", version="1.0.0")
        class TestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        assert "test_plugin" in registry.list_plugins()
        assert registry.count == 1
    
    def test_unregister_plugin(self, registry):
        """Test plugin unregistration."""
        @shadow_plugin(name="unregister_test")
        class UnregisterTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        assert registry.unregister("unregister_test")
        assert "unregister_test" not in registry.list_plugins()
    
    def test_get_plugin(self, registry):
        """Test getting plugin by name."""
        @shadow_plugin(name="get_test")
        class GetTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        plugin_class = registry.get("get_test")
        assert plugin_class is not None
    
    def test_get_nonexistent_plugin(self, registry):
        """Test getting non-existent plugin."""
        with pytest.raises(PluginNotFoundError):
            registry.get("nonexistent")
    
    def test_duplicate_registration(self, registry):
        """Test duplicate registration error."""
        @shadow_plugin(name="duplicate_test")
        class DuplicateTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        with pytest.raises(PluginRegistrationError):
            registry.register(DuplicateTestPlugin, name="duplicate_test")
    
    def test_get_metadata(self, registry):
        """Test getting plugin metadata."""
        @shadow_plugin(name="meta_test", version="2.0.0")
        class MetaTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        meta = registry.get_metadata("meta_test")
        assert meta['version'] == "2.0.0"
    
    def test_get_by_sensor_type(self, registry):
        """Test getting plugins by sensor type."""
        @shadow_plugin(name="acoustic_test", sensor_type=SensorType.ACOUSTIC)
        class AcousticTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        acoustic_plugins = registry.get_by_sensor_type(SensorType.ACOUSTIC)
        assert "acoustic_test" in acoustic_plugins


# =============================================================================
# TEST: SHADOW PLUGIN
# =============================================================================

class TestShadowPlugin:
    """Test ShadowPlugin base class."""
    
    def test_plugin_initialization(self):
        """Test plugin initialization."""
        @shadow_plugin(name="init_test")
        class InitTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        plugin = InitTestPlugin()
        assert plugin.initialize()
        assert plugin.is_initialized
        plugin.shutdown()
    
    def test_plugin_processing(self, sample_shadow_data):
        """Test plugin processing."""
        @shadow_plugin(name="process_test")
        class ProcessTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                data.stage = ProcessingStage.RECONSTRUCTED
                return data
        
        plugin = ProcessTestPlugin()
        plugin.initialize()
        
        result = plugin.process(sample_shadow_data)
        assert result.stage == ProcessingStage.RECONSTRUCTED
        
        plugin.shutdown()
    
    def test_uninitialized_processing(self, sample_shadow_data):
        """Test processing without initialization."""
        @shadow_plugin(name="uninit_test")
        class UninitTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        plugin = UninitTestPlugin()
        
        with pytest.raises(ProcessingError):
            plugin.process(sample_shadow_data)
    
    def test_plugin_info(self):
        """Test plugin info retrieval."""
        @shadow_plugin(name="info_test", version="1.2.3")
        class InfoTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        plugin = InfoTestPlugin()
        info = plugin.get_info()
        assert info['name'] == "info_test"
        assert info['version'] == "1.2.3"


# =============================================================================
# TEST: SHADOW ENGINE CORE
# =============================================================================

class TestShadowEngineCore:
    """Test ShadowEngineCore functionality."""
    
    def test_engine_creation(self):
        """Test engine creation."""
        config = EngineConfig(max_latency_ms=10.0)
        engine = ShadowEngineCore(config)
        assert engine.config.max_latency_ms == 10.0
    
    def test_plugin_loading(self):
        """Test plugin loading."""
        @shadow_plugin(name="load_test")
        class LoadTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        engine = ShadowEngineCore()
        plugin = engine.load_plugin("load_test")
        assert plugin is not None
        assert "load_test" in engine.loaded_plugins
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        @shadow_plugin(name="engine_init_test")
        class EngineInitTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        engine = ShadowEngineCore()
        engine.load_plugin("engine_init_test")
        assert engine.initialize()
        assert engine.is_initialized
        engine.shutdown()
    
    def test_data_processing(self, sample_shadow_data):
        """Test data processing through engine."""
        @shadow_plugin(name="engine_process_test")
        class EngineProcessTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                data.stage = ProcessingStage.RECONSTRUCTED
                return data
        
        engine = ShadowEngineCore()
        engine.load_plugin("engine_process_test")
        engine.initialize()
        
        result = engine.process(sample_shadow_data)
        assert result.stage == ProcessingStage.RECONSTRUCTED
        
        engine.shutdown()
    
    def test_tracking_interface(self, sample_raw_data):
        """Test high-level tracking interface."""
        @shadow_plugin(name="track_test")
        class TrackTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                # Create a dummy contour
                points = np.array([[0.1, 0, 0], [0, 0.1, 0], [-0.1, 0, 0]])
                data.contour = ShadowContour(
                    points=points,
                    confidence=np.array([0.9, 0.9, 0.9]),
                    centroid=Vector3D(0, 0, 0),
                    area=0.01
                )
                data.stage = ProcessingStage.RECONSTRUCTED
                return data
        
        engine = ShadowEngineCore()
        engine.load_plugin("track_test")
        engine.initialize()
        
        result = engine.track(sample_raw_data)
        assert isinstance(result, TrackingResult)
        
        engine.shutdown()
    
    def test_engine_stats(self, sample_shadow_data):
        """Test engine statistics."""
        @shadow_plugin(name="stats_test")
        class StatsTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        engine = ShadowEngineCore()
        engine.load_plugin("stats_test")
        engine.initialize()
        
        # Process some frames
        for _ in range(10):
            engine.process(sample_shadow_data)
        
        stats = engine.get_stats()
        assert stats['frame_count'] == 10
        assert 'latency_ms' in stats
        
        engine.shutdown()


# =============================================================================
# TEST: PROCESSING PIPELINE
# =============================================================================

class TestProcessingPipeline:
    """Test ProcessingPipeline functionality."""
    
    def test_pipeline_creation(self):
        """Test pipeline creation."""
        pipeline = ProcessingPipeline()
        assert pipeline is not None
    
    def test_processor_addition(self):
        """Test adding processors to pipeline."""
        pipeline = ProcessingPipeline()
        
        class TestProcessor(ShadowProcessor):
            def process(self, data):
                return data
        
        processor = TestProcessor()
        pipeline.add(processor)
        
        # Test method chaining
        result = pipeline.add(processor)
        assert result is pipeline
    
    def test_pipeline_processing(self, sample_shadow_data):
        """Test data processing through pipeline."""
        pipeline = ProcessingPipeline()
        
        class StageProcessor(ShadowProcessor):
            def process(self, data):
                data.stage = ProcessingStage.BEAMFORMED
                return data
        
        pipeline.add(StageProcessor())
        
        result = pipeline.process(sample_shadow_data)
        assert result.stage == ProcessingStage.BEAMFORMED


class TestTemporalSmoother:
    """Test TemporalSmoother processor."""
    
    def test_smoother_creation(self):
        """Test smoother creation."""
        smoother = TemporalSmoother(alpha=0.8, buffer_size=10)
        assert smoother.alpha == 0.8
        assert smoother.buffer_size == 10
    
    def test_smoothing(self, sample_shadow_data):
        """Test temporal smoothing."""
        smoother = TemporalSmoother(alpha=0.5)
        
        # Add contour to data
        points = np.array([[0.1, 0, 0], [0, 0.1, 0], [-0.1, 0, 0]])
        sample_shadow_data.contour = ShadowContour(
            points=points,
            confidence=np.array([0.9, 0.9, 0.9]),
            centroid=Vector3D(0.1, 0.1, 0),
            area=0.01
        )
        
        # Process multiple frames
        for _ in range(5):
            result = smoother.process(sample_shadow_data.copy())
        
        assert result.contour is not None


class TestConfidenceFilter:
    """Test ConfidenceFilter processor."""
    
    def test_filter_creation(self):
        """Test filter creation."""
        filter_proc = ConfidenceFilter(threshold=0.7)
        assert filter_proc.threshold == 0.7
    
    def test_low_confidence_filtering(self, sample_shadow_data):
        """Test filtering of low-confidence contours."""
        filter_proc = ConfidenceFilter(threshold=0.8)
        
        # Add low-confidence contour
        points = np.array([[0.1, 0, 0], [0, 0.1, 0], [-0.1, 0, 0]])
        sample_shadow_data.contour = ShadowContour(
            points=points,
            confidence=np.array([0.3, 0.3, 0.3]),  # Low confidence
            centroid=Vector3D(0, 0, 0),
            area=0.01
        )
        
        result = filter_proc.process(sample_shadow_data)
        assert result.contour is None


# =============================================================================
# TEST: UTILITY FUNCTIONS
# =============================================================================

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_compute_bounding_box(self):
        """Test bounding box computation."""
        points = np.array([
            [0, 0, 0],
            [1, 1, 1],
            [0.5, 0.5, 0.5]
        ])
        
        min_corner, max_corner = compute_bounding_box(points)
        assert min_corner.x == 0.0
        assert max_corner.x == 1.0
    
    def test_compute_centroid(self):
        """Test centroid computation."""
        points = np.array([
            [0, 0, 0],
            [2, 0, 0],
            [0, 2, 0]
        ])
        
        centroid = compute_centroid(points)
        assert centroid.x == 2/3
        assert centroid.y == 2/3
    
    def test_estimate_surface_area(self):
        """Test surface area estimation."""
        # Square contour
        points = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0]
        ])
        
        area = estimate_surface_area(points)
        assert area > 0


# =============================================================================
# TEST: PERFORMANCE BENCHMARKS
# =============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""
    
    def test_plugin_registration_time(self, registry):
        """Benchmark plugin registration time."""
        def register_plugin():
            @shadow_plugin(name=f"perf_test_{time.time()}")
            class PerfTestPlugin(ShadowPlugin):
                def _on_initialize(self):
                    return True
                def _on_shutdown(self):
                    pass
                def _process_impl(self, data):
                    return data
        
        # Benchmark registration
        times = []
        for i in range(100):
            t0 = time.perf_counter()
            register_plugin()
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1e6)  # microseconds
        
        mean_time = np.mean(times)
        # Registration should be < 100 microseconds
        assert mean_time < 100, f"Registration took {mean_time:.1f} µs (target: <100 µs)"
    
    def test_plugin_load_time(self, registry):
        """Benchmark plugin load time."""
        @shadow_plugin(name="load_perf_test")
        class LoadPerfTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                return data
        
        engine = ShadowEngineCore()
        
        # Benchmark loading
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            engine.load_plugin("load_perf_test")
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)  # milliseconds
        
        mean_time = np.mean(times)
        # Loading should be < 1 ms
        assert mean_time < 1.0, f"Loading took {mean_time:.3f} ms (target: <1 ms)"
    
    def test_data_processing_latency(self, sample_shadow_data):
        """Benchmark data processing latency."""
        @shadow_plugin(name="latency_test")
        class LatencyTestPlugin(ShadowPlugin):
            def _on_initialize(self):
                return True
            def _on_shutdown(self):
                pass
            def _process_impl(self, data):
                # Minimal processing
                return data
        
        engine = ShadowEngineCore()
        engine.load_plugin("latency_test")
        engine.initialize()
        
        # Benchmark processing
        times = []
        for _ in range(1000):
            t0 = time.perf_counter()
            engine.process(sample_shadow_data)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)  # milliseconds
        
        engine.shutdown()
        
        p99_time = np.percentile(times, 99)
        # P99 latency should be < 10 ms
        assert p99_time < 10.0, f"P99 latency {p99_time:.3f} ms (target: <10 ms)"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
