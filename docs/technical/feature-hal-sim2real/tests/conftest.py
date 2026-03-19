"""
Pytest configuration and fixtures for HAL tests.
"""

from __future__ import annotations

import numpy as np
import pytest

from ..hal.base import HardwareConfig, CalibrationData
from ..sim2real.bridge import (
    SimulatedMicrophoneArray,
    SimulatedTransducer,
    SimulatedGlove,
)


@pytest.fixture
def hardware_config() -> HardwareConfig:
    """Default hardware configuration for tests."""
    return HardwareConfig(
        sample_rate=48000,
        buffer_size=1024,
        num_channels=4,
    )


@pytest.fixture
def hardware_config_8ch() -> HardwareConfig:
    """8-channel hardware configuration for tests."""
    return HardwareConfig(
        sample_rate=48000,
        buffer_size=1024,
        num_channels=8,
    )


@pytest.fixture
def simulated_microphone_array(hardware_config: HardwareConfig) -> SimulatedMicrophoneArray:
    """Simulated microphone array fixture."""
    mics = SimulatedMicrophoneArray(hardware_config)
    yield mics
    mics.close()


@pytest.fixture
def simulated_transducer(hardware_config: HardwareConfig) -> SimulatedTransducer:
    """Simulated transducer fixture."""
    transducer = SimulatedTransducer(hardware_config, frequency=40000)
    yield transducer
    transducer.close()


@pytest.fixture
def simulated_glove(hardware_config: HardwareConfig) -> SimulatedGlove:
    """Simulated glove fixture."""
    glove = SimulatedGlove(hardware_config)
    yield glove
    glove.close()


@pytest.fixture
def sample_calibration() -> CalibrationData:
    """Sample calibration data fixture."""
    return CalibrationData(
        gain_calibration=np.array([1.0, 1.02, 0.98, 1.01]),
        time_offset=np.array([0.0, 1e-6, -1e-6, 0.0]),
        phase_calibration=np.array([0.0, 0.1, -0.1, 0.0]),
        microphone_positions=np.array([
            [0.015, 0.0, 0.0],
            [0.0, 0.015, 0.0],
            [-0.015, 0.0, 0.0],
            [0.0, -0.015, 0.0],
        ]),
        quality_score=0.95,
    )


@pytest.fixture
def noisy_calibration() -> CalibrationData:
    """Noisy calibration data fixture (for validation testing)."""
    return CalibrationData(
        gain_calibration=np.array([1.0, 2.0, 0.5, 1.0]),
        time_offset=np.array([0.0, 1e-5, -1e-5, 0.0]),
        gain_uncertainty=np.array([0.5, 0.5, 0.5, 0.5]),
        time_uncertainty=np.array([1e-6, 1e-6, 1e-6, 1e-6]),
        quality_score=0.5,
    )


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> None:
    """Create temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")


# Markers for conditional test execution
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "hardware: marks tests that require hardware")
    config.addinivalue_line("markers", "raspberry_pi: marks tests that require Raspberry Pi")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip hardware tests by default."""
    skip_hardware = pytest.mark.skip(reason="Hardware test - use --hardware to run")
    skip_rpi = pytest.mark.skip(reason="Raspberry Pi test - use --raspberry-pi to run")
    
    for item in items:
        if "hardware" in item.keywords and not config.getoption("--hardware"):
            item.add_marker(skip_hardware)
        if "raspberry_pi" in item.keywords and not config.getoption("--raspberry-pi"):
            item.add_marker(skip_rpi)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--hardware",
        action="store_true",
        default=False,
        help="Run hardware tests",
    )
    parser.addoption(
        "--raspberry-pi",
        action="store_true",
        default=False,
        help="Run Raspberry Pi specific tests",
    )
