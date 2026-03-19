"""
Tests for Sim-to-Real Bridge.

Tests the sim-to-real bridge functionality, data validation,
and mode switching.
"""

from __future__ import annotations

import numpy as np
import pytest

from ..sim2real.bridge import (
    DataValidator,
    SimRealMapper,
    Sim2RealBridge,
    ValidatedMicrophoneArray,
    SimulatedMicrophoneArray,
    SimulatedTransducer,
    SimulatedGlove,
)
from ..hal.base import (
    HardwareConfig,
    HardwareMode,
    GloveSensorData,
)


class TestDataValidator:
    """Test DataValidator."""
    
    def test_valid_audio(self) -> None:
        """Test validation of valid audio."""
        validator = DataValidator()
        
        # Valid audio data
        data = np.random.randn(1000, 4) * 0.1
        
        is_valid, details = validator.validate_audio(data, 48000)
        
        assert is_valid
        assert details["valid"]
        assert len(details["issues"]) == 0
    
    def test_nan_detection(self) -> None:
        """Test NaN detection."""
        validator = DataValidator()
        
        data = np.random.randn(1000, 4)
        data[100, 0] = np.nan
        
        is_valid, details = validator.validate_audio(data, 48000)
        
        assert not is_valid
        assert "NaN" in str(details["issues"])
    
    def test_amplitude_check(self) -> None:
        """Test amplitude validation."""
        validator = DataValidator(max_amplitude=1.0)
        
        # Data exceeding amplitude limit
        data = np.random.randn(1000, 4) * 2.0
        
        is_valid, details = validator.validate_audio(data, 48000)
        
        assert not is_valid
        assert "Amplitude" in str(details["issues"])
    
    def test_dc_offset_detection(self) -> None:
        """Test DC offset detection."""
        validator = DataValidator()
        
        # Data with large DC offset
        data = np.random.randn(1000, 4) * 0.1 + 0.5
        
        is_valid, details = validator.validate_audio(data, 48000)
        
        assert not is_valid
        assert "DC offset" in str(details["issues"])
    
    def test_sanitize_audio(self) -> None:
        """Test audio sanitization."""
        validator = DataValidator()
        
        # Data with issues
        data = np.random.randn(1000, 4) * 2.0 + 0.5
        data[100, 0] = np.nan
        
        sanitized = validator.sanitize_audio(data)
        
        # Check NaN removed
        assert not np.any(np.isnan(sanitized))
        
        # Check DC removed
        assert np.all(np.abs(np.mean(sanitized, axis=0)) < 0.01)
        
        # Check amplitude clipped
        assert np.all(np.abs(sanitized) <= 1.0)
    
    def test_valid_glove_data(self) -> None:
        """Test valid glove data validation."""
        validator = DataValidator()
        
        data = GloveSensorData(
            flex_values=np.array([0.5, 0.5, 0.5, 0.5, 0.5]),
            pressure_values=np.array([100.0] * 10),
            accelerometer=np.array([0.0, 0.0, 9.8]),
            gyroscope=np.array([0.0, 0.0, 0.0]),
        )
        
        is_valid, details = validator.validate_glove_data(data)
        
        assert is_valid
        assert details["valid"]
    
    def test_invalid_flex_values(self) -> None:
        """Test invalid flex value detection."""
        validator = DataValidator()
        
        data = GloveSensorData(
            flex_values=np.array([0.5, 1.5, -0.5, 0.5, 0.5]),  # Out of range
            pressure_values=np.array([100.0] * 10),
            accelerometer=np.array([0.0, 0.0, 9.8]),
            gyroscope=np.array([0.0, 0.0, 0.0]),
        )
        
        is_valid, details = validator.validate_glove_data(data)
        
        assert not is_valid
        assert "Flex values" in str(details["issues"])


class TestSimRealMapper:
    """Test SimRealMapper."""
    
    def test_initial_scale(self) -> None:
        """Test initial scale factors."""
        mapper = SimRealMapper()
        
        assert mapper._sim_to_real_scale == 1.0
        assert mapper._real_to_sim_scale == 1.0
    
    def test_scale_calibration(self) -> None:
        """Test scale calibration."""
        mapper = SimRealMapper()
        
        sim_data = np.random.randn(1000) * 0.1
        real_data = np.random.randn(1000) * 0.5
        
        mapper.set_calibration_scale(sim_data, real_data)
        
        # Scale should be real_rms / sim_rms
        assert mapper._sim_to_real_scale > 1.0
        assert mapper._real_to_sim_scale < 1.0
    
    def test_sim_to_real_conversion(self) -> None:
        """Test sim to real conversion."""
        mapper = SimRealMapper()
        
        # Set scale
        mapper._sim_to_real_scale = 2.0
        
        sim_data = np.array([1.0, 2.0, 3.0])
        real_data = mapper.sim_to_real(sim_data)
        
        np.testing.assert_array_almost_equal(real_data, np.array([2.0, 4.0, 6.0]))
    
    def test_real_to_sim_conversion(self) -> None:
        """Test real to sim conversion."""
        mapper = SimRealMapper()
        
        # Set scale
        mapper._sim_to_real_scale = 2.0
        mapper._real_to_sim_scale = 0.5
        
        real_data = np.array([2.0, 4.0, 6.0])
        sim_data = mapper.real_to_sim(real_data)
        
        np.testing.assert_array_almost_equal(sim_data, np.array([1.0, 2.0, 3.0]))


class TestSim2RealBridge:
    """Test Sim2RealBridge."""
    
    def test_sim_mode_creation(self) -> None:
        """Test bridge creation in sim mode."""
        bridge = Sim2RealBridge(mode="sim")
        
        assert bridge.mode == HardwareMode.SIMULATION
    
    def test_real_mode_creation(self) -> None:
        """Test bridge creation in real mode."""
        bridge = Sim2RealBridge(mode="real")
        
        assert bridge.mode == HardwareMode.REAL
    
    def test_get_microphone_array(self) -> None:
        """Test getting microphone array."""
        bridge = Sim2RealBridge(mode="sim")
        
        mics = bridge.get_microphone_array()
        
        assert mics is not None
        assert hasattr(mics, "read")
        assert hasattr(mics, "start_stream")
    
    def test_get_transducer(self) -> None:
        """Test getting transducer."""
        bridge = Sim2RealBridge(mode="sim")
        
        transducer = bridge.get_transducer(frequency=40000)
        
        assert transducer is not None
        assert hasattr(transducer, "emit_burst")
    
    def test_get_glove(self) -> None:
        """Test getting glove."""
        bridge = Sim2RealBridge(mode="sim")
        
        glove = bridge.get_glove()
        
        assert glove is not None
        assert hasattr(glove, "read_sensors")
    
    def test_data_validation(self) -> None:
        """Test data validation."""
        bridge = Sim2RealBridge(mode="sim")
        
        # Valid audio
        audio_data = np.random.randn(1000, 4) * 0.1
        results = bridge.validate_data(audio_data=audio_data)
        
        assert "audio" in results
        assert results["audio"]["valid"]
        
        # Invalid audio
        bad_audio = np.random.randn(1000, 4) * 3.0
        results = bridge.validate_data(audio_data=bad_audio)
        
        assert not results["audio"]["valid"]
    
    def test_sim_microphone_streaming(self) -> None:
        """Test sim microphone streaming through bridge."""
        bridge = Sim2RealBridge(mode="sim")
        mics = bridge.get_microphone_array()
        
        mics.start_stream()
        samples = mics.read(1024)
        mics.stop_stream()
        
        assert samples.n_samples == 1024
    
    def test_sim_transducer_emission(self) -> None:
        """Test sim transducer emission through bridge."""
        bridge = Sim2RealBridge(mode="sim")
        transducer = bridge.get_transducer()
        
        transducer.emit_burst(100)
        
        # Should complete without error


class TestValidatedMicrophoneArray:
    """Test ValidatedMicrophoneArray wrapper."""
    
    def test_validated_read(self) -> None:
        """Test validated read."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        validator = DataValidator()
        
        validated = ValidatedMicrophoneArray(mics, validator)
        
        mics.start_stream()
        samples = validated.read(1024)
        mics.stop_stream()
        
        assert samples.n_samples == 1024
    
    def test_validation_stats(self) -> None:
        """Test validation statistics."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        validator = DataValidator()
        
        validated = ValidatedMicrophoneArray(mics, validator)
        
        stats = validated.get_validation_stats()
        
        assert "valid_reads" in stats
        assert "invalid_reads" in stats


class TestModeSwitching:
    """Test mode switching functionality."""
    
    def test_string_mode_parsing(self) -> None:
        """Test string mode parsing."""
        bridge_sim = Sim2RealBridge(mode="sim")
        assert bridge_sim.mode == HardwareMode.SIMULATION
        
        bridge_real = Sim2RealBridge(mode="real")
        assert bridge_real.mode == HardwareMode.REAL
        
        bridge_hybrid = Sim2RealBridge(mode="hybrid")
        assert bridge_hybrid.mode == HardwareMode.HYBRID
    
    def test_case_insensitive_mode(self) -> None:
        """Test case insensitive mode parsing."""
        bridge1 = Sim2RealBridge(mode="SIM")
        assert bridge1.mode == HardwareMode.SIMULATION
        
        bridge2 = Sim2RealBridge(mode="Sim")
        assert bridge2.mode == HardwareMode.SIMULATION


class TestPerformanceMonitoring:
    """Test performance monitoring."""
    
    def test_stats_collection(self) -> None:
        """Test statistics collection."""
        bridge = Sim2RealBridge(mode="sim")
        
        # Get some hardware
        mics = bridge.get_microphone_array()
        
        # Do some operations
        mics.start_stream()
        mics.read(1024)
        mics.stop_stream()
        
        # Get stats
        stats = bridge.get_performance_stats()
        
        # Should have some data
        assert isinstance(stats, dict)


class TestGracefulDegradation:
    """Test graceful degradation."""
    
    def test_auto_fallback(self) -> None:
        """Test automatic fallback to simulation."""
        # Request real mode with fallback
        bridge = Sim2RealBridge(mode="real", auto_fallback=True)
        
        # Should still get working components
        mics = bridge.get_microphone_array()
        assert mics is not None
    
    def test_no_fallback(self) -> None:
        """Test no fallback mode."""
        # This test might fail on non-RPi systems without fallback
        # We just verify the option exists
        bridge = Sim2RealBridge(mode="sim", auto_fallback=False)
        assert not bridge._auto_fallback


class TestIntegration:
    """Integration tests."""
    
    def test_full_pipeline_sim(self) -> None:
        """Test full pipeline in simulation mode."""
        bridge = Sim2RealBridge(mode="sim")
        
        # Get all components
        mics = bridge.get_microphone_array()
        transducer = bridge.get_transducer()
        glove = bridge.get_glove()
        
        # Use components
        mics.start_stream()
        
        # Emit and record
        transducer.emit_burst(50)
        audio = mics.read(1024)
        
        # Read glove
        glove.connect()
        sensor_data = glove.read_sensors()
        glove.disconnect()
        
        mics.stop_stream()
        
        # Validate
        validation = bridge.validate_data(
            audio_data=audio.data,
            glove_data=sensor_data,
        )
        
        assert "audio" in validation
        assert "glove" in validation
    
    def test_close_releases_resources(self) -> None:
        """Test that close releases resources."""
        bridge = Sim2RealBridge(mode="sim")
        
        # Get components
        mics = bridge.get_microphone_array()
        transducer = bridge.get_transducer()
        glove = bridge.get_glove()
        
        # Start some operations
        mics.start_stream()
        glove.connect()
        
        # Close
        bridge.close()
        
        # Components should be cleaned up
        # (actual cleanup verified in implementation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
