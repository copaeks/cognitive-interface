"""
Unit Tests for Universal Shadow Engine Plugins
===============================================

Comprehensive tests for all plugin implementations.

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

from core.data import (
    ShadowData, ShadowContour, RawSensorData, TrackingResult,
    SensorType, ProcessingStage, Vector3D, Timestamp, ShadowQuality
)
from core.engine import PluginRegistry, shadow_plugin

# Import plugins
from plugins.acoustic import AcousticPlugin, AcousticConfig
from plugins.em import EMPlugin, EMConfig
from plugins.thz import THzPlugin, THzConfig
from plugins.photoacoustic import PhotoacousticPlugin, PhotoacousticConfig


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def clean_registry():
    """Clean plugin registry before each test."""
    registry = PluginRegistry()
    registry.clear()
    yield
    registry.clear()


@pytest.fixture
def sample_acoustic_signals():
    """Create sample acoustic microphone signals."""
    return np.random.randn(4, 2048).astype(np.float32)


@pytest.fixture
def sample_raw_acoustic_data(sample_acoustic_signals):
    """Create sample raw acoustic sensor data."""
    return RawSensorData(
        sensor_type=SensorType.ACOUSTIC,
        raw_data=sample_acoustic_signals,
        sample_rate=96000,
        timestamp=Timestamp()
    )


@pytest.fixture
def sample_shadow_acoustic_data(sample_raw_acoustic_data):
    """Create sample shadow data for acoustic plugin."""
    return ShadowData(
        frame_id=1,
        sensor_type=SensorType.ACOUSTIC,
        raw_data=sample_raw_acoustic_data,
        stage=ProcessingStage.RAW
    )


# =============================================================================
# TEST: ACOUSTIC PLUGIN
# =============================================================================

class TestAcousticPlugin:
    """Test AcousticPlugin implementation."""
    
    def test_plugin_registration(self):
        """Test that acoustic plugin is registered."""
        registry = PluginRegistry()
        assert "acoustic" in registry.list_plugins()
        
        meta = registry.get_metadata("acoustic")
        assert meta['version'] == "2.0.0"
        assert meta['sensor_type'] == SensorType.ACOUSTIC
    
    def test_config_creation(self):
        """Test AcousticConfig creation."""
        config = AcousticConfig(
            sample_rate=96000,
            n_mics=4,
            mic_spacing=0.021
        )
        assert config.sample_rate == 96000
        assert config.n_mics == 4
    
    def test_config_validation(self):
        """Test AcousticConfig validation."""
        with pytest.raises(ValueError):
            # Sample rate too low for Nyquist
            AcousticConfig(sample_rate=40000, frequency_max=40000)
        
        with pytest.raises(ValueError):
            # Not enough microphones
            AcousticConfig(n_mics=1)
    
    def test_plugin_creation(self):
        """Test AcousticPlugin creation."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        assert plugin.name == "acoustic"
        assert plugin.sensor_type == SensorType.ACOUSTIC
    
    def test_plugin_initialization(self):
        """Test AcousticPlugin initialization."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        assert plugin.initialize()
        assert plugin.is_initialized
        plugin.shutdown()
    
    def test_signal_extraction(self, sample_shadow_acoustic_data):
        """Test microphone signal extraction."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        signals = plugin._extract_signals(sample_shadow_acoustic_data.raw_data)
        assert signals is not None
        assert signals.shape[0] == 4  # 4 microphones
        
        plugin.shutdown()
    
    def test_beamforming(self, sample_acoustic_signals):
        """Test beamforming computation."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        # Compute STFT
        spectra = plugin._compute_stft_all_mics(sample_acoustic_signals)
        assert spectra.shape[0] == 4  # 4 microphones
        
        # Beamform
        beamformer_output = plugin._beamform(spectra)
        assert len(beamformer_output) == config.n_beam_angles
        assert np.all(beamformer_output >= 0)  # Power is non-negative
        
        plugin.shutdown()
    
    def test_shadow_detection(self, sample_acoustic_signals):
        """Test shadow detection."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        spectra = plugin._compute_stft_all_mics(sample_acoustic_signals)
        beamformer_output = plugin._beamform(spectra)
        shadow_angles = plugin._detect_shadows(beamformer_output)
        
        # Should detect some angles (random data may have variations)
        assert isinstance(shadow_angles, np.ndarray)
        
        plugin.shutdown()
    
    def test_contour_reconstruction(self, sample_acoustic_signals):
        """Test contour reconstruction."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        spectra = plugin._compute_stft_all_mics(sample_acoustic_signals)
        beamformer_output = plugin._beamform(spectra)
        shadow_angles = plugin._detect_shadows(beamformer_output)
        
        if len(shadow_angles) >= 3:
            contour = plugin._reconstruct_contour(shadow_angles, beamformer_output)
            assert contour is not None
            assert len(contour.points) > 0
            assert contour.is_valid()
        
        plugin.shutdown()
    
    def test_full_processing_pipeline(self, sample_shadow_acoustic_data):
        """Test full processing pipeline."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        result = plugin.process(sample_shadow_acoustic_data)
        
        assert result.stage in [ProcessingStage.RECONSTRUCTED, ProcessingStage.DETECTED]
        assert result.processing_time_ms > 0
        
        plugin.shutdown()
    
    def test_plugin_info(self):
        """Test plugin info retrieval."""
        config = AcousticConfig(sample_rate=96000, n_mics=4)
        plugin = AcousticPlugin(config)
        
        info = plugin.get_info()
        assert info['name'] == "acoustic"
        assert info['sample_rate'] == 96000
        assert info['n_mics'] == 4
    
    def test_default_factory(self):
        """Test default plugin factory."""
        from plugins.acoustic import create_default_acoustic_plugin
        plugin = create_default_acoustic_plugin()
        assert plugin.name == "acoustic"
        assert isinstance(plugin.config, AcousticConfig)


# =============================================================================
# TEST: EM PLUGIN
# =============================================================================

class TestEMPlugin:
    """Test EMPlugin implementation."""
    
    def test_plugin_registration(self):
        """Test that EM plugin is registered."""
        registry = PluginRegistry()
        assert "em" in registry.list_plugins()
        
        meta = registry.get_metadata("em")
        assert meta['version'] == "0.1.0"
        assert meta['sensor_type'] == SensorType.ELECTROMAGNETIC
    
    def test_config_creation(self):
        """Test EMConfig creation."""
        config = EMConfig(
            frequency_hz=5.9e9,
            n_antennas=8
        )
        assert config.frequency_hz == 5.9e9
        assert config.n_antennas == 8
    
    def test_plugin_creation(self):
        """Test EMPlugin creation."""
        config = EMConfig()
        plugin = EMPlugin(config)
        assert plugin.name == "em"
        assert plugin.sensor_type == SensorType.ELECTROMAGNETIC
    
    def test_plugin_initialization(self):
        """Test EMPlugin initialization."""
        config = EMConfig()
        plugin = EMPlugin(config)
        assert plugin.initialize()
        assert plugin.is_initialized
        plugin.shutdown()
    
    def test_stub_processing(self):
        """Test stub processing."""
        config = EMConfig()
        plugin = EMPlugin(config)
        plugin.initialize()
        
        # Create dummy data
        raw_data = RawSensorData(
            sensor_type=SensorType.ELECTROMAGNETIC,
            raw_data=np.random.randn(8, 100).astype(np.float32),
            sample_rate=1000
        )
        data = ShadowData(raw_data=raw_data)
        
        result = plugin.process(data)
        
        # Stub should produce a contour
        assert result.contour is not None
        assert result.stage == ProcessingStage.RECONSTRUCTED
        
        plugin.shutdown()
    
    def test_plugin_info(self):
        """Test plugin info retrieval."""
        config = EMConfig(frequency_hz=5.9e9)
        plugin = EMPlugin(config)
        
        info = plugin.get_info()
        assert info['name'] == "em"
        assert info['frequency_ghz'] == 5.9
        assert info['is_stub'] is True


# =============================================================================
# TEST: THZ PLUGIN
# =============================================================================

class TestTHzPlugin:
    """Test THzPlugin implementation."""
    
    def test_plugin_registration(self):
        """Test that THz plugin is registered."""
        registry = PluginRegistry()
        assert "thz" in registry.list_plugins()
        
        meta = registry.get_metadata("thz")
        assert meta['version'] == "0.1.0"
        assert meta['sensor_type'] == SensorType.TERAHERTZ
    
    def test_config_creation(self):
        """Test THzConfig creation."""
        config = THzConfig(
            frequency_hz=300e9,
            array_size=64
        )
        assert config.frequency_hz == 300e9
        assert config.array_size == 64
    
    def test_plugin_creation(self):
        """Test THzPlugin creation."""
        config = THzConfig()
        plugin = THzPlugin(config)
        assert plugin.name == "thz"
        assert plugin.sensor_type == SensorType.TERAHERTZ
    
    def test_plugin_initialization(self):
        """Test THzPlugin initialization."""
        config = THzConfig()
        plugin = THzPlugin(config)
        assert plugin.initialize()
        plugin.shutdown()
    
    def test_stub_processing(self):
        """Test stub processing."""
        config = THzConfig()
        plugin = THzPlugin(config)
        plugin.initialize()
        
        # Create dummy data
        raw_data = RawSensorData(
            sensor_type=SensorType.TERAHERTZ,
            raw_data=np.random.randn(64, 64).astype(np.float32),
            sample_rate=1000
        )
        data = ShadowData(raw_data=raw_data)
        
        result = plugin.process(data)
        
        # Stub should produce a high-resolution contour
        assert result.contour is not None
        assert len(result.contour.points) == 64  # Higher resolution
        
        plugin.shutdown()
    
    def test_plugin_info(self):
        """Test plugin info retrieval."""
        config = THzConfig(frequency_hz=300e9, array_size=64)
        plugin = THzPlugin(config)
        
        info = plugin.get_info()
        assert info['name'] == "thz"
        assert info['frequency_ghz'] == 300.0
        assert info['array_size'] == 64


# =============================================================================
# TEST: PHOTOACOUSTIC PLUGIN
# =============================================================================

class TestPhotoacousticPlugin:
    """Test PhotoacousticPlugin implementation."""
    
    def test_plugin_registration(self):
        """Test that photoacoustic plugin is registered."""
        registry = PluginRegistry()
        assert "photoacoustic" in registry.list_plugins()
        
        meta = registry.get_metadata("photoacoustic")
        assert meta['version'] == "0.1.0"
        assert meta['sensor_type'] == SensorType.PHOTOACOUSTIC
    
    def test_config_creation(self):
        """Test PhotoacousticConfig creation."""
        config = PhotoacousticConfig(
            laser_wavelength_nm=1064,
            laser_energy_mj=20
        )
        assert config.laser_wavelength_nm == 1064
        assert config.laser_energy_mj == 20
    
    def test_plugin_creation(self):
        """Test PhotoacousticPlugin creation."""
        config = PhotoacousticConfig()
        plugin = PhotoacousticPlugin(config)
        assert plugin.name == "photoacoustic"
        assert plugin.sensor_type == SensorType.PHOTOACOUSTIC
    
    def test_plugin_initialization(self):
        """Test PhotoacousticPlugin initialization."""
        config = PhotoacousticConfig()
        plugin = PhotoacousticPlugin(config)
        assert plugin.initialize()
        plugin.shutdown()
    
    def test_stub_processing(self):
        """Test stub processing."""
        config = PhotoacousticConfig()
        plugin = PhotoacousticPlugin(config)
        plugin.initialize()
        
        # Create dummy data
        raw_data = RawSensorData(
            sensor_type=SensorType.PHOTOACOUSTIC,
            raw_data=np.random.randn(128, 1000).astype(np.float32),
            sample_rate=1000000
        )
        data = ShadowData(raw_data=raw_data)
        
        result = plugin.process(data)
        
        # Stub should produce an elliptical contour
        assert result.contour is not None
        assert len(result.contour.points) == 48
        
        plugin.shutdown()
    
    def test_plugin_info(self):
        """Test plugin info retrieval."""
        config = PhotoacousticConfig(laser_wavelength_nm=1064)
        plugin = PhotoacousticPlugin(config)
        
        info = plugin.get_info()
        assert info['name'] == "photoacoustic"
        assert info['laser_wavelength_nm'] == 1064


# =============================================================================
# TEST: PERFORMANCE BENCHMARKS
# =============================================================================

class TestPluginPerformance:
    """Performance benchmarks for plugins."""
    
    def test_acoustic_plugin_latency(self, sample_shadow_acoustic_data):
        """Benchmark acoustic plugin processing latency."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        # Warm-up
        for _ in range(10):
            plugin.process(sample_shadow_acoustic_data.copy())
        
        # Benchmark
        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            plugin.process(sample_shadow_acoustic_data.copy())
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
        
        plugin.shutdown()
        
        p99_time = np.percentile(times, 99)
        mean_time = np.mean(times)
        
        print(f"\nAcoustic Plugin Latency:")
        print(f"  Mean: {mean_time:.3f} ms")
        print(f"  P99: {p99_time:.3f} ms")
        
        # P99 should be < 10 ms
        assert p99_time < 10.0, f"P99 latency {p99_time:.3f} ms (target: <10 ms)"
    
    def test_acoustic_plugin_throughput(self, sample_shadow_acoustic_data):
        """Benchmark acoustic plugin throughput."""
        config = AcousticConfig()
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        # Warm-up
        for _ in range(10):
            plugin.process(sample_shadow_acoustic_data.copy())
        
        # Benchmark
        n_iterations = 1000
        t0 = time.perf_counter()
        for _ in range(n_iterations):
            plugin.process(sample_shadow_acoustic_data.copy())
        t1 = time.perf_counter()
        
        plugin.shutdown()
        
        elapsed = t1 - t0
        throughput = n_iterations / elapsed
        
        print(f"\nAcoustic Plugin Throughput:")
        print(f"  {throughput:.0f} fps")
        
        # Should achieve > 100 fps
        assert throughput > 100, f"Throughput {throughput:.0f} fps (target: >100 fps)"


# =============================================================================
# TEST: PLUGIN COMPATIBILITY
# =============================================================================

class TestPluginCompatibility:
    """Test compatibility between plugins."""
    
    def test_all_plugins_registered(self):
        """Test that all expected plugins are registered."""
        registry = PluginRegistry()
        plugins = registry.list_plugins()
        
        expected = ["acoustic", "em", "thz", "photoacoustic"]
        for plugin in expected:
            assert plugin in plugins, f"Plugin {plugin} not registered"
    
    def test_plugin_sensor_types(self):
        """Test that plugins have correct sensor types."""
        registry = PluginRegistry()
        
        assert registry.get_metadata("acoustic")['sensor_type'] == SensorType.ACOUSTIC
        assert registry.get_metadata("em")['sensor_type'] == SensorType.ELECTROMAGNETIC
        assert registry.get_metadata("thz")['sensor_type'] == SensorType.TERAHERTZ
        assert registry.get_metadata("photoacoustic")['sensor_type'] == SensorType.PHOTOACOUSTIC


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
