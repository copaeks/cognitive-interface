"""
Tests for Hardware Abstraction Layer.

Tests the base HAL interfaces, factory, and simulated components.
"""

from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path
import tempfile

from ..hal.base import (
    CalibrationData,
    HardwareConfig,
    HardwareMode,
    SampleBuffer,
)
from ..hal.factory import HardwareFactory, create_microphone_array, create_glove
from ..sim2real.bridge import (
    SimulatedMicrophoneArray,
    SimulatedTransducer,
    SimulatedGlove,
)


class TestHardwareConfig:
    """Test HardwareConfig dataclass."""
    
    def test_default_config(self) -> None:
        """Test default configuration."""
        config = HardwareConfig()
        assert config.sample_rate == 48000
        assert config.buffer_size == 1024
        assert config.num_channels == 4
    
    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = HardwareConfig(
            sample_rate=96000,
            buffer_size=2048,
            num_channels=8,
        )
        assert config.sample_rate == 96000
        assert config.buffer_size == 2048
        assert config.num_channels == 8
    
    def test_serialization(self) -> None:
        """Test config serialization."""
        config = HardwareConfig(sample_rate=48000, num_channels=4)
        data = config.to_dict()
        
        restored = HardwareConfig.from_dict(data)
        assert restored.sample_rate == config.sample_rate
        assert restored.num_channels == config.num_channels


class TestCalibrationData:
    """Test CalibrationData dataclass."""
    
    def test_default_calibration(self) -> None:
        """Test default calibration."""
        cal = CalibrationData()
        assert len(cal.gain_calibration) == 4
        assert len(cal.time_offset) == 4
        assert cal.microphone_positions.shape == (4, 3)
    
    def test_custom_calibration(self) -> None:
        """Test custom calibration values."""
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.1, 0.9, 1.0]),
            time_offset=np.array([0.0, 1e-6, -1e-6, 0.0]),
        )
        assert cal.gain_calibration[1] == 1.1
        assert cal.time_offset[1] == 1e-6
    
    def test_save_load(self) -> None:
        """Test calibration save/load."""
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.1, 0.9, 1.0]),
            quality_score=0.95,
        )
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        
        try:
            cal.save(path)
            loaded = CalibrationData.load(path)
            
            np.testing.assert_array_almost_equal(
                loaded.gain_calibration,
                cal.gain_calibration,
            )
            assert loaded.quality_score == cal.quality_score
        finally:
            path.unlink(missing_ok=True)


class TestSampleBuffer:
    """Test SampleBuffer dataclass."""
    
    def test_buffer_creation(self) -> None:
        """Test buffer creation."""
        data = np.random.randn(1000, 4)
        buffer = SampleBuffer(data=data, sample_rate=48000)
        
        assert buffer.n_samples == 1000
        assert buffer.n_channels == 4
        assert buffer.duration == pytest.approx(1000 / 48000, rel=1e-3)
    
    def test_get_channel(self) -> None:
        """Test channel extraction."""
        data = np.random.randn(1000, 4)
        buffer = SampleBuffer(data=data, sample_rate=48000)
        
        ch0 = buffer.get_channel(0)
        np.testing.assert_array_equal(ch0, data[:, 0])
    
    def test_slice_time(self) -> None:
        """Test time slicing."""
        data = np.random.randn(48000, 4)  # 1 second
        buffer = SampleBuffer(data=data, sample_rate=48000)
        
        sliced = buffer.slice_time(0.1, 0.2)  # 100ms slice
        assert sliced.duration == pytest.approx(0.1, rel=1e-3)


class TestHardwareFactory:
    """Test HardwareFactory."""
    
    def test_factory_creation(self) -> None:
        """Test factory creation."""
        factory = HardwareFactory(mode=HardwareMode.SIMULATION)
        assert factory.mode == HardwareMode.SIMULATION
    
    def test_platform_detection(self) -> None:
        """Test platform detection."""
        factory = HardwareFactory()
        assert factory.platform in ["macos", "linux", "windows", "unknown", "arm_linux"]
    
    def test_create_sim_microphone_array(self) -> None:
        """Test creating simulated microphone array."""
        factory = HardwareFactory(mode=HardwareMode.SIMULATION)
        config = HardwareConfig()
        
        mics = factory.create_microphone_array(config)
        assert isinstance(mics, (SimulatedMicrophoneArray,))
        assert mics.num_microphones == config.num_channels
    
    def test_create_sim_glove(self) -> None:
        """Test creating simulated glove."""
        factory = HardwareFactory(mode=HardwareMode.SIMULATION)
        config = HardwareConfig()
        
        glove = factory.create_glove(config)
        assert isinstance(glove, SimulatedGlove)


class TestSimulatedMicrophoneArray:
    """Test SimulatedMicrophoneArray."""
    
    def test_creation(self) -> None:
        """Test array creation."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        
        assert mics.num_microphones == 4
        assert mics.sample_rate == 48000
    
    def test_streaming(self) -> None:
        """Test streaming functionality."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        
        mics.start_stream()
        assert mics.is_streaming
        
        samples = mics.read(1024)
        assert samples.n_samples == 1024
        assert samples.n_channels == 4
        
        mics.stop_stream()
        assert not mics.is_streaming
    
    def test_add_tone_source(self) -> None:
        """Test adding tone source."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        
        mics.add_tone_source(frequency=1000, amplitude=0.5)
        
        mics.start_stream()
        samples = mics.read(4800)  # 100ms
        mics.stop_stream()
        
        # Check that signal is present
        assert np.max(np.abs(samples.data)) > 0.1
    
    def test_calibration(self) -> None:
        """Test calibration application."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 2.0, 1.0, 1.0]),
        )
        mics.set_calibration(cal)
        
        mics.start_stream()
        samples = mics.read(1024)
        mics.stop_stream()
        
        # Channel 1 should have 2x amplitude
        rms = np.sqrt(np.mean(samples.data ** 2, axis=0))
        assert rms[1] > rms[0] * 1.5  # Should be roughly 2x


class TestSimulatedTransducer:
    """Test SimulatedTransducer."""
    
    def test_creation(self) -> None:
        """Test transducer creation."""
        config = HardwareConfig()
        transducer = SimulatedTransducer(config, frequency=40000)
        
        assert transducer.frequency == 40000
        assert not transducer.is_emitting
    
    def test_emission(self) -> None:
        """Test emission."""
        config = HardwareConfig()
        transducer = SimulatedTransducer(config, frequency=40000)
        
        transducer.start()
        assert transducer.is_emitting
        
        transducer.stop()
        assert not transducer.is_emitting
    
    def test_burst(self) -> None:
        """Test burst emission."""
        config = HardwareConfig()
        transducer = SimulatedTransducer(config, frequency=40000)
        
        transducer.emit_burst(100)
        
        log = transducer.get_emission_log()
        assert len(log) == 1
        assert log[0]["type"] == "burst"
        assert log[0]["duration_ms"] == 100
    
    def test_frequency_change(self) -> None:
        """Test frequency change."""
        config = HardwareConfig()
        transducer = SimulatedTransducer(config, frequency=40000)
        
        transducer.set_frequency(50000)
        assert transducer.frequency == 50000


class TestSimulatedGlove:
    """Test SimulatedGlove."""
    
    def test_creation(self) -> None:
        """Test glove creation."""
        config = HardwareConfig()
        glove = SimulatedGlove(config)
        
        assert glove.num_flex_sensors == 5
        assert glove.num_pressure_sensors == 10
        assert glove.has_imu
    
    def test_connection(self) -> None:
        """Test connection."""
        config = HardwareConfig()
        glove = SimulatedGlove(config)
        
        assert not glove.is_connected
        
        glove.connect()
        assert glove.is_connected
        
        glove.disconnect()
        assert not glove.is_connected
    
    def test_sensor_reading(self) -> None:
        """Test sensor reading."""
        config = HardwareConfig()
        glove = SimulatedGlove(config)
        
        glove.connect()
        data = glove.read_sensors()
        glove.disconnect()
        
        assert len(data.flex_values) == 5
        assert len(data.pressure_values) == 10
        assert len(data.accelerometer) == 3
        assert len(data.gyroscope) == 3
        
        # Check flex values are in range
        assert np.all(data.flex_values >= 0)
        assert np.all(data.flex_values <= 1)
    
    def test_vibration(self) -> None:
        """Test vibration setting."""
        config = HardwareConfig()
        glove = SimulatedGlove(config)
        
        glove.connect()
        glove.set_vibration(0.5, "pulse")
        glove.disconnect()
        
        # Should complete without error


class TestConvenienceFunctions:
    """Test convenience factory functions."""
    
    def test_create_microphone_array(self) -> None:
        """Test create_microphone_array function."""
        mics = create_microphone_array("sim")
        assert isinstance(mics, (SimulatedMicrophoneArray,))
    
    def test_create_glove(self) -> None:
        """Test create_glove function."""
        glove = create_glove("sim")
        assert isinstance(glove, SimulatedGlove)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
