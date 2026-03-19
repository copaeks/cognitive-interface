"""
Tests for Calibration Module.

Tests auto calibration procedures and uncertainty quantification.
"""

from __future__ import annotations

import numpy as np
import pytest

from ..calibration.auto_calibrate import (
    ArrayCalibrator,
    CalibrationResult,
    ToneCalibration,
    ImpulseCalibration,
)
from ..calibration.uncertainty import (
    UncertaintyEstimator,
    UncertaintyBudget,
    CalibrationValidator,
)
from ..hal.base import CalibrationData, HardwareConfig
from ..sim2real.bridge import (
    SimulatedMicrophoneArray,
    SimulatedTransducer,
)


class TestUncertaintyBudget:
    """Test UncertaintyBudget."""
    
    def test_empty_budget(self) -> None:
        """Test empty uncertainty budget."""
        budget = UncertaintyBudget()
        assert budget.combined_uncertainty() == 0.0
    
    def test_single_component(self) -> None:
        """Test budget with single component."""
        budget = UncertaintyBudget()
        budget.add_component("test", 0.1, "normal")
        
        assert budget.combined_uncertainty() == pytest.approx(0.1)
    
    def test_multiple_components(self) -> None:
        """Test budget with multiple components."""
        budget = UncertaintyBudget()
        budget.add_component("A", 0.1, "normal")
        budget.add_component("B", 0.2, "normal")
        
        # Combined = sqrt(0.1^2 + 0.2^2)
        expected = np.sqrt(0.01 + 0.04)
        assert budget.combined_uncertainty() == pytest.approx(expected)
    
    def test_expanded_uncertainty(self) -> None:
        """Test expanded uncertainty."""
        budget = UncertaintyBudget()
        budget.add_component("test", 0.1, "normal")
        
        # k=2 for 95% confidence
        assert budget.expanded_uncertainty(2.0) == pytest.approx(0.2)


class TestUncertaintyEstimator:
    """Test UncertaintyEstimator."""
    
    def test_gain_uncertainty(self) -> None:
        """Test gain uncertainty estimation."""
        estimator = UncertaintyEstimator()
        
        # Create measurements with known variance
        measurements = [
            np.array([1.0, 1.0, 1.0, 1.0]) + np.random.randn(4) * 0.01
            for _ in range(100)
        ]
        
        uncertainty = estimator.estimate_gain_uncertainty(measurements)
        
        assert len(uncertainty) == 4
        assert np.all(uncertainty > 0)
        assert np.all(uncertainty < 0.01)  # Should be less than std
    
    def test_time_uncertainty(self) -> None:
        """Test time uncertainty estimation."""
        estimator = UncertaintyEstimator()
        
        measurements = [
            np.array([0.0, 1e-6, -1e-6, 0.0]) + np.random.randn(4) * 1e-7
            for _ in range(100)
        ]
        
        uncertainty = estimator.estimate_time_uncertainty(measurements, 48000)
        
        assert len(uncertainty) == 4
        assert np.all(uncertainty > 0)
    
    def test_position_uncertainty(self) -> None:
        """Test position uncertainty estimation."""
        estimator = UncertaintyEstimator()
        
        # Position estimates with noise
        true_pos = np.array([[0.01, 0, 0], [0, 0.01, 0], [-0.01, 0, 0], [0, -0.01, 0]])
        estimates = [
            true_pos + np.random.randn(4, 3) * 0.001
            for _ in range(50)
        ]
        
        uncertainty = estimator.estimate_position_uncertainty(estimates)
        
        assert uncertainty.shape == (4, 3)
        assert np.all(uncertainty > 0)
    
    def test_calibration_budget(self) -> None:
        """Test calibration budget creation."""
        estimator = UncertaintyEstimator()
        
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.0, 1.0, 1.0]),
            gain_uncertainty=np.array([0.01, 0.01, 0.01, 0.01]),
        )
        
        budgets = estimator.create_calibration_budget(cal)
        
        assert "gain" in budgets
        assert "time" in budgets
        assert "position" in budgets
        
        assert budgets["gain"].combined_uncertainty() > 0


class TestCalibrationValidator:
    """Test CalibrationValidator."""
    
    def test_gain_validation(self) -> None:
        """Test gain calibration validation."""
        validator = CalibrationValidator()
        
        # Valid calibration
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.02, 0.98, 1.01]),
            gain_uncertainty=np.array([0.01, 0.01, 0.01, 0.01]),
        )
        
        result = validator.validate_gain_calibration(cal)
        assert result["valid"]
        assert result["uncertainty_ok"]
    
    def test_gain_validation_failure(self) -> None:
        """Test gain validation with bad calibration."""
        validator = CalibrationValidator()
        
        # Invalid calibration - large variation
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 2.0, 0.5, 1.0]),
            gain_uncertainty=np.array([0.5, 0.5, 0.5, 0.5]),
        )
        
        result = validator.validate_gain_calibration(cal)
        assert not result["valid"]
    
    def test_time_validation(self) -> None:
        """Test time calibration validation."""
        validator = CalibrationValidator()
        
        cal = CalibrationData(
            time_offset=np.array([0.0, 1e-6, -1e-6, 0.0]),
            time_uncertainty=np.array([1e-7, 1e-7, 1e-7, 1e-7]),
        )
        
        result = validator.validate_time_calibration(cal)
        assert result["valid"]
    
    def test_position_validation(self) -> None:
        """Test position calibration validation."""
        validator = CalibrationValidator()
        
        cal = CalibrationData(
            microphone_positions=np.array([
                [0.015, 0, 0],
                [0, 0.015, 0],
                [-0.015, 0, 0],
                [0, -0.015, 0],
            ]),
            position_uncertainty=np.zeros((4, 3)),
        )
        
        result = validator.validate_position_calibration(cal)
        assert result["valid"]
    
    def test_full_validation(self) -> None:
        """Test full validation suite."""
        validator = CalibrationValidator()
        
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.0, 1.0, 1.0]),
            time_offset=np.array([0.0, 0.0, 0.0, 0.0]),
            microphone_positions=np.array([
                [0.015, 0, 0],
                [0, 0.015, 0],
                [-0.015, 0, 0],
                [0, -0.015, 0],
            ]),
            quality_score=0.95,
        )
        
        result = validator.full_validation(cal)
        assert result["valid"]
        assert "recommendations" in result


class TestToneCalibration:
    """Test ToneCalibration procedure."""
    
    def test_calibration_creation(self) -> None:
        """Test calibration procedure creation."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        transducer = SimulatedTransducer(config, frequency=40000)
        
        cal = ToneCalibration(mics, transducer, frequencies=[1000, 2000])
        
        assert cal.get_name() == "ToneCalibration"
    
    def test_calibration_run(self) -> None:
        """Test running calibration."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        
        # Add a tone source
        mics.add_tone_source(frequency=1000, amplitude=0.5)
        
        transducer = SimulatedTransducer(config, frequency=40000)
        
        cal = ToneCalibration(mics, transducer, frequencies=[1000])
        result = cal.run()
        
        assert isinstance(result, CalibrationResult)
        # Note: May fail in pure simulation without proper signal injection


class TestImpulseCalibration:
    """Test ImpulseCalibration procedure."""
    
    def test_calibration_creation(self) -> None:
        """Test calibration procedure creation."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        transducer = SimulatedTransducer(config, frequency=40000)
        
        cal = ImpulseCalibration(mics, transducer)
        
        assert cal.get_name() == "ImpulseCalibration"


class TestArrayCalibrator:
    """Test ArrayCalibrator."""
    
    def test_calibrator_creation(self) -> None:
        """Test calibrator creation."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        transducer = SimulatedTransducer(config, frequency=40000)
        
        calibrator = ArrayCalibrator(mics, transducer)
        
        assert calibrator._mics == mics
        assert calibrator._transducer == transducer
    
    def test_full_calibration(self) -> None:
        """Test full calibration run."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        transducer = SimulatedTransducer(config, frequency=40000)
        
        calibrator = ArrayCalibrator(mics, transducer)
        
        # Run calibration (may be partial in simulation)
        result = calibrator.calibrate()
        
        assert isinstance(result, CalibrationResult)
        assert isinstance(result.calibration, CalibrationData)
        assert 0.0 <= result.quality_score <= 1.0
    
    def test_calibration_validation(self) -> None:
        """Test calibration validation."""
        config = HardwareConfig(num_channels=4)
        mics = SimulatedMicrophoneArray(config)
        transducer = SimulatedTransducer(config, frequency=40000)
        
        calibrator = ArrayCalibrator(mics, transducer)
        
        # Create a calibration
        cal = CalibrationData(
            gain_calibration=np.array([1.0, 1.0, 1.0, 1.0]),
        )
        
        # Validate
        validation = calibrator.validate_calibration(cal, num_tests=3)
        
        assert "gain_consistency" in validation


class TestMonteCarloValidation:
    """Test Monte Carlo uncertainty validation."""
    
    def test_monte_carlo(self) -> None:
        """Test Monte Carlo simulation."""
        estimator = UncertaintyEstimator(num_monte_carlo_samples=1000)
        
        # Simple calibration function
        def cal_func(inputs: np.ndarray) -> CalibrationData:
            return CalibrationData(
                gain_calibration=np.array([1.0, 1.0, 1.0, 1.0]) + inputs[0],
            )
        
        input_dists = [("normal", 0.0, 0.01)]
        
        result = estimator.monte_carlo_validation(cal_func, input_dists)
        
        assert "gain_mean" in result
        assert "gain_std" in result
        assert result["n_samples"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
