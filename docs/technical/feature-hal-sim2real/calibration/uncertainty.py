"""
Uncertainty Quantification for Calibration.

Provides statistical methods for estimating and tracking uncertainty
in calibration parameters. Implements GUM (Guide to the Expression
of Uncertainty in Measurement) methodology.

Features:
- Type A uncertainty (statistical)
- Type B uncertainty (systematic)
- Uncertainty propagation
- Monte Carlo validation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from ..hal.base import CalibrationData, SampleBuffer


logger = logging.getLogger(__name__)


@dataclass
class UncertaintyComponent:
    """Single uncertainty component."""
    name: str
    value: float  # Standard uncertainty
    distribution: str  # 'normal', 'uniform', 'triangular'
    degrees_of_freedom: float = np.inf
    description: str = ""
    
    def expanded_uncertainty(self, coverage_factor: float = 2.0) -> float:
        """Get expanded uncertainty (default k=2 for 95% confidence)."""
        return self.value * coverage_factor


@dataclass
class UncertaintyBudget:
    """Complete uncertainty budget for a measurement."""
    components: list[UncertaintyComponent] = field(default_factory=list)
    sensitivity_coefficients: NDArray[np.float64] | None = None
    correlation_matrix: NDArray[np.float64] | None = None
    
    def combined_uncertainty(self) -> float:
        """Compute combined standard uncertainty."""
        if not self.components:
            return 0.0
        
        # Sum of squares (uncorrelated)
        variances = [c.value ** 2 for c in self.components]
        return float(np.sqrt(sum(variances)))
    
    def expanded_uncertainty(self, coverage_factor: float = 2.0) -> float:
        """Compute expanded uncertainty."""
        return self.combined_uncertainty() * coverage_factor
    
    def effective_degrees_of_freedom(self) -> float:
        """Compute effective degrees of freedom (Welch-Satterthwaite)."""
        if not self.components:
            return np.inf
        
        uc = self.combined_uncertainty()
        if uc == 0:
            return np.inf
        
        numerator = uc ** 4
        denominator = sum(
            (c.value ** 4) / c.degrees_of_freedom
            for c in self.components
            if c.degrees_of_freedom > 0
        )
        
        return numerator / (denominator + 1e-10)
    
    def coverage_factor(self, confidence_level: float = 0.95) -> float:
        """Get coverage factor for desired confidence level."""
        df = self.effective_degrees_of_freedom()
        
        if np.isinf(df):
            # Normal distribution
            return stats.norm.ppf((1 + confidence_level) / 2)
        else:
            # t-distribution
            return stats.t.ppf((1 + confidence_level) / 2, df)
    
    def add_component(
        self,
        name: str,
        value: float,
        distribution: str = "normal",
        df: float = np.inf,
        description: str = "",
    ) -> None:
        """Add uncertainty component."""
        self.components.append(UncertaintyComponent(
            name=name,
            value=value,
            distribution=distribution,
            degrees_of_freedom=df,
            description=description,
        ))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "components": [
                {
                    "name": c.name,
                    "value": c.value,
                    "distribution": c.distribution,
                    "degrees_of_freedom": c.degrees_of_freedom,
                    "description": c.description,
                }
                for c in self.components
            ],
            "combined_uncertainty": self.combined_uncertainty(),
            "expanded_uncertainty_k2": self.expanded_uncertainty(2.0),
            "effective_df": self.effective_degrees_of_freedom(),
        }


class UncertaintyEstimator:
    """
    Estimate uncertainty in calibration parameters.
    
    Uses statistical methods and Monte Carlo simulation to
    quantify uncertainty in microphone array calibration.
    """
    
    def __init__(self, num_monte_carlo_samples: int = 10000) -> None:
        """
        Initialize uncertainty estimator.
        
        Args:
            num_monte_carlo_samples: Number of MC samples for validation
        """
        self._n_mc = num_monte_carlo_samples
    
    def estimate_gain_uncertainty(
        self,
        measurements: list[NDArray[np.float64]],
        confidence_level: float = 0.95,
    ) -> NDArray[np.float64]:
        """
        Estimate gain calibration uncertainty.
        
        Args:
            measurements: List of gain measurements per channel
            confidence_level: Confidence level for intervals
        
        Returns:
            Standard uncertainty per channel
        """
        if not measurements:
            return np.array([])
        
        # Stack measurements
        data = np.array(measurements)  # Shape: (n_measurements, n_channels)
        
        # Compute standard deviation for each channel
        std = np.std(data, axis=0, ddof=1)
        
        # Standard uncertainty = std / sqrt(n)
        n = len(measurements)
        uncertainty = std / np.sqrt(n)
        
        return uncertainty
    
    def estimate_time_uncertainty(
        self,
        time_measurements: list[NDArray[np.float64]],
        sample_rate: float,
    ) -> NDArray[np.float64]:
        """
        Estimate time offset uncertainty.
        
        Args:
            time_measurements: List of time offset measurements
            sample_rate: Sample rate in Hz
        
        Returns:
            Standard uncertainty per channel (seconds)
        """
        if not time_measurements:
            return np.array([])
        
        data = np.array(time_measurements)
        
        # Statistical uncertainty
        std = np.std(data, axis=0, ddof=1)
        n = len(time_measurements)
        stat_uncertainty = std / np.sqrt(n)
        
        # Quantization uncertainty (sample period / sqrt(12))
        quant_uncertainty = (1.0 / sample_rate) / np.sqrt(12)
        
        # Combine
        return np.sqrt(stat_uncertainty ** 2 + quant_uncertainty ** 2)
    
    def estimate_position_uncertainty(
        self,
        position_estimates: list[NDArray[np.float64]],
    ) -> NDArray[np.float64]:
        """
        Estimate microphone position uncertainty.
        
        Args:
            position_estimates: List of position estimates (n, 3) per estimate
        
        Returns:
            Standard uncertainty per microphone (x, y, z)
        """
        if not position_estimates:
            return np.array([])
        
        # Stack estimates
        data = np.array(position_estimates)  # Shape: (n_estimates, n_mics, 3)
        
        # Compute covariance for each microphone
        n_mics = data.shape[1]
        uncertainties = np.zeros((n_mics, 3))
        
        for mic in range(n_mics):
            mic_data = data[:, mic, :]  # Shape: (n_estimates, 3)
            
            # Standard deviation for each coordinate
            uncertainties[mic] = np.std(mic_data, axis=0, ddof=1)
        
        return uncertainties
    
    def monte_carlo_validation(
        self,
        calibration_func: Callable[[NDArray[np.float64]], CalibrationData],
        input_distributions: list[tuple[str, float, float]],
    ) -> dict[str, Any]:
        """
        Validate uncertainty estimates using Monte Carlo.
        
        Args:
            calibration_func: Function that takes random inputs and returns calibration
            input_distributions: List of (distribution, mean, std) for each input
        
        Returns:
            MC validation results
        """
        logger.info(f"Running Monte Carlo with {self._n_mc} samples")
        
        results: list[CalibrationData] = []
        
        for _ in range(self._n_mc):
            # Generate random inputs
            inputs = []
            for dist, mean, std in input_distributions:
                if dist == "normal":
                    inputs.append(np.random.normal(mean, std))
                elif dist == "uniform":
                    inputs.append(np.random.uniform(mean - std, mean + std))
            
            # Run calibration
            result = calibration_func(np.array(inputs))
            results.append(result)
        
        # Analyze results
        gain_values = np.array([r.gain_calibration for r in results])
        time_values = np.array([r.time_offset for r in results])
        
        return {
            "gain_mean": np.mean(gain_values, axis=0),
            "gain_std": np.std(gain_values, axis=0),
            "gain_ci_95": np.percentile(gain_values, [2.5, 97.5], axis=0),
            "time_mean": np.mean(time_values, axis=0),
            "time_std": np.std(time_values, axis=0),
            "time_ci_95": np.percentile(time_values, [2.5, 97.5], axis=0),
            "n_samples": self._n_mc,
        }
    
    def create_calibration_budget(
        self,
        calibration: CalibrationData,
        measurement_conditions: dict[str, Any] | None = None,
    ) -> dict[str, UncertaintyBudget]:
        """
        Create complete uncertainty budget for calibration.
        
        Args:
            calibration: Calibration data
            measurement_conditions: Environmental conditions
        
        Returns:
            Dictionary of budgets per parameter
        """
        budgets = {}
        
        # Gain uncertainty budget
        gain_budget = UncertaintyBudget()
        gain_budget.add_component(
            "measurement_repeatability",
            np.mean(calibration.gain_uncertainty) if np.any(calibration.gain_uncertainty) else 0.01,
            "normal",
            description="Repeatability of gain measurements",
        )
        gain_budget.add_component(
            "temperature_effect",
            0.005,  # 0.5% typical
            "uniform",
            description="Temperature variation effect on sensitivity",
        )
        gain_budget.add_component(
            "frequency_response",
            0.01,  # 1% typical
            "uniform",
            description="Frequency response variation",
        )
        budgets["gain"] = gain_budget
        
        # Time uncertainty budget
        time_budget = UncertaintyBudget()
        time_budget.add_component(
            "sample_quantization",
            1.0 / 48000 / np.sqrt(12),  # For 48kHz
            "uniform",
            description="ADC sample quantization",
        )
        time_budget.add_component(
            "measurement_jitter",
            1e-6,  # 1 microsecond
            "normal",
            description="Timing jitter",
        )
        budgets["time"] = time_budget
        
        # Position uncertainty budget
        position_budget = UncertaintyBudget()
        position_budget.add_component(
            "measurement_precision",
            np.mean(calibration.position_uncertainty) if np.any(calibration.position_uncertainty) else 0.001,
            "normal",
            description="Position measurement precision",
        )
        position_budget.add_component(
            "thermal_expansion",
            0.0001,  # 0.1mm
            "uniform",
            description="Thermal expansion of array structure",
        )
        budgets["position"] = position_budget
        
        return budgets


class CalibrationValidator:
    """
    Validate calibration quality and detect issues.
    """
    
    def __init__(self) -> None:
        """Initialize validator."""
        self._estimator = UncertaintyEstimator()
    
    def validate_gain_calibration(
        self,
        calibration: CalibrationData,
        max_gain_variation: float = 0.1,  # 10%
    ) -> dict[str, Any]:
        """
        Validate gain calibration.
        
        Args:
            calibration: Calibration to validate
            max_gain_variation: Maximum allowed gain variation
        
        Returns:
            Validation results
        """
        gains = calibration.gain_calibration
        
        # Check for outliers
        gain_range = np.max(gains) - np.min(gains)
        gain_mean = np.mean(gains)
        relative_variation = gain_range / (gain_mean + 1e-10)
        
        # Check uncertainty
        uncertainty_ok = np.all(calibration.gain_uncertainty < max_gain_variation / 3)
        
        issues = []
        if relative_variation > max_gain_variation:
            issues.append(f"Gain variation {relative_variation:.3f} exceeds limit")
        if not uncertainty_ok:
            issues.append("Gain uncertainty too high")
        
        return {
            "valid": len(issues) == 0,
            "gain_range": float(gain_range),
            "relative_variation": float(relative_variation),
            "uncertainty_ok": uncertainty_ok,
            "issues": issues,
        }
    
    def validate_time_calibration(
        self,
        calibration: CalibrationData,
        max_time_error: float = 1e-5,  # 10 microseconds
    ) -> dict[str, Any]:
        """
        Validate time calibration.
        
        Args:
            calibration: Calibration to validate
            max_time_error: Maximum allowed time error
        
        Returns:
            Validation results
        """
        time_offsets = calibration.time_offset
        
        # Check for excessive offsets
        max_offset = np.max(np.abs(time_offsets))
        
        # Check uncertainty
        uncertainty_ok = np.all(calibration.time_uncertainty < max_time_error / 3)
        
        issues = []
        if max_offset > max_time_error:
            issues.append(f"Max time offset {max_offset:.2e}s exceeds limit")
        if not uncertainty_ok:
            issues.append("Time uncertainty too high")
        
        return {
            "valid": len(issues) == 0,
            "max_offset": float(max_offset),
            "uncertainty_ok": uncertainty_ok,
            "issues": issues,
        }
    
    def validate_position_calibration(
        self,
        calibration: CalibrationData,
        expected_spacing: float = 0.015,  # 1.5cm
        tolerance: float = 0.005,  # 0.5cm
    ) -> dict[str, Any]:
        """
        Validate microphone position calibration.
        
        Args:
            calibration: Calibration to validate
            expected_spacing: Expected microphone spacing
            tolerance: Allowed deviation
        
        Returns:
            Validation results
        """
        positions = calibration.microphone_positions
        
        # Check for reasonable positions
        position_magnitudes = np.linalg.norm(positions, axis=1)
        
        # Compute pairwise distances
        n_mics = len(positions)
        distances = []
        for i in range(n_mics):
            for j in range(i + 1, n_mics):
                dist = np.linalg.norm(positions[i] - positions[j])
                distances.append(dist)
        
        distances = np.array(distances)
        
        # Check spacing consistency
        spacing_std = np.std(distances)
        spacing_mean = np.mean(distances)
        
        issues = []
        if spacing_std > tolerance:
            issues.append(f"Spacing variation {spacing_std:.4f}m exceeds tolerance")
        
        # Check uncertainty
        position_unc = calibration.position_uncertainty
        uncertainty_ok = np.all(position_unc < tolerance / 3)
        if not uncertainty_ok:
            issues.append("Position uncertainty too high")
        
        return {
            "valid": len(issues) == 0,
            "mean_spacing": float(spacing_mean),
            "spacing_std": float(spacing_std),
            "uncertainty_ok": uncertainty_ok,
            "issues": issues,
        }
    
    def full_validation(
        self,
        calibration: CalibrationData,
    ) -> dict[str, Any]:
        """
        Run full validation suite.
        
        Args:
            calibration: Calibration to validate
        
        Returns:
            Complete validation results
        """
        gain_val = self.validate_gain_calibration(calibration)
        time_val = self.validate_time_calibration(calibration)
        position_val = self.validate_position_calibration(calibration)
        
        all_valid = gain_val["valid"] and time_val["valid"] and position_val["valid"]
        
        return {
            "valid": all_valid,
            "gain": gain_val,
            "time": time_val,
            "position": position_val,
            "overall_quality": calibration.quality_score,
            "recommendations": self._generate_recommendations(
                gain_val, time_val, position_val
            ),
        }
    
    def _generate_recommendations(
        self,
        gain_val: dict[str, Any],
        time_val: dict[str, Any],
        position_val: dict[str, Any],
    ) -> list[str]:
        """Generate recommendations based on validation."""
        recommendations = []
        
        if not gain_val["valid"]:
            recommendations.append("Re-run gain calibration in quieter environment")
        
        if not time_val["valid"]:
            recommendations.append("Check microphone connections and re-run time calibration")
        
        if not position_val["valid"]:
            recommendations.append("Verify physical array geometry")
        
        if not recommendations:
            recommendations.append("Calibration is valid and ready for use")
        
        return recommendations


def compute_coverage_intervals(
    values: NDArray[np.float64],
    confidence_level: float = 0.95,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Compute coverage intervals for calibration parameters.
    
    Args:
        values: Array of values (n_samples, n_parameters)
        confidence_level: Desired confidence level
    
    Returns:
        (lower_bounds, upper_bounds) for each parameter
    """
    alpha = 1 - confidence_level
    lower_percentile = alpha / 2 * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower = np.percentile(values, lower_percentile, axis=0)
    upper = np.percentile(values, upper_percentile, axis=0)
    
    return lower, upper
