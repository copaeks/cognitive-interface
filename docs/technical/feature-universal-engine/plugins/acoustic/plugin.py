"""
Acoustic Shadow Plugin
======================

PAST (Passive Acoustic Shadow Tracking) plugin implementation.
Provides ultrasonic shadow detection using 4-microphone array beamforming.

Based on the Shadow Principle: detect absence of signal (shadow) 
rather than presence of reflection for O(1) complexity.

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, List
import time

try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    # Create dummy decorators for when numba is not available
    def jit(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper if args and callable(args[0]) else wrapper
    prange = range

try:
    from scipy import signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.engine import ShadowPlugin, shadow_plugin
from core.data import (
    ShadowData, ShadowContour, RawSensorData, SensorType,
    ProcessingStage, PluginConfig, Vector3D, Timestamp, ShadowQuality,
    compute_centroid, estimate_surface_area
)


# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================

SPEED_OF_SOUND = 343.0  # m/s at 20°C
AIR_DENSITY = 1.225  # kg/m³


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass(slots=True)
class AcousticConfig(PluginConfig):
    """Configuration for acoustic shadow plugin.
    
    Attributes:
        sample_rate: Sampling frequency in Hz (default: 96000)
        n_mics: Number of microphones (default: 4)
        mic_spacing: Distance between microphones in meters (default: 0.021)
        frequency_min: Minimum ultrasonic frequency in Hz (default: 20000)
        frequency_max: Maximum ultrasonic frequency in Hz (default: 40000)
        frame_size: STFT frame size (default: 512)
        hop_size: STFT hop size (default: 256)
        threshold_db: Shadow detection threshold in dB (default: -30)
        n_beam_angles: Number of beamforming angles (default: 360)
        enable_numba: Enable numba JIT optimization (default: True)
    """
    sample_rate: int = 96000
    n_mics: int = 4
    mic_spacing: float = 0.021  # 21mm optimal spacing
    frequency_min: float = 20000  # 20 kHz
    frequency_max: float = 40000  # 40 kHz
    frame_size: int = 512
    hop_size: int = 256
    threshold_db: float = -30.0
    n_beam_angles: int = 360
    enable_numba: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.sample_rate < 2 * self.frequency_max:
            raise ValueError("Sample rate must be >= 2 * frequency_max (Nyquist)")
        if self.n_mics < 2:
            raise ValueError("At least 2 microphones required for beamforming")
        if self.mic_spacing <= 0:
            raise ValueError("Microphone spacing must be positive")


# =============================================================================
# ACOUSTIC PLUGIN
# =============================================================================

@shadow_plugin(
    name="acoustic",
    version="2.0.0",
    sensor_type=SensorType.ACOUSTIC
)
class AcousticPlugin(ShadowPlugin):
    """Acoustic shadow tracking plugin using 4-microphone array.
    
    Implements O(1) complexity shadow reconstruction through:
    1. Delay-and-sum beamforming (pre-computed steering vectors)
    2. Shadow region detection from power minima
    3. Contour reconstruction from angular shadow boundaries
    
    The Shadow Principle: Instead of O(n³) iterative optimization,
    we directly detect the shadow boundary through beamforming.
    
    Example:
        config = AcousticConfig(sample_rate=96000, n_mics=4)
        plugin = AcousticPlugin(config)
        plugin.initialize()
        
        # Process microphone signals (n_mics, n_samples)
        signals = np.random.randn(4, 2048)
        raw_data = RawSensorData(
            sensor_type=SensorType.ACOUSTIC,
            raw_data=signals,
            sample_rate=96000
        )
        data = ShadowData(raw_data=raw_data)
        result = plugin.process(data)
    """
    
    def __init__(self, config: Optional[PluginConfig] = None) -> None:
        """Initialize acoustic plugin.
        
        Args:
            config: Acoustic configuration. Uses defaults if None.
        """
        # Convert generic config to acoustic config if needed
        if config is None:
            config = AcousticConfig()
        elif not isinstance(config, AcousticConfig):
            # Convert from generic PluginConfig
            acoustic_config = AcousticConfig(
                name=config.name,
                enabled=config.enabled,
                priority=config.priority
            )
            acoustic_config.parameters.update(config.parameters)
            config = acoustic_config
        
        super().__init__(config)
        self.acoustic_config: AcousticConfig = config
        
        # Computed attributes
        self._mic_positions: Optional[np.ndarray] = None
        self._steering_vectors: Optional[np.ndarray] = None
        self._freq_indices: Optional[np.ndarray] = None
        self._beam_angles: Optional[np.ndarray] = None
        
    def _on_initialize(self) -> bool:
        """Initialize the acoustic plugin.
        
        Pre-computes steering vectors for O(1) beamforming.
        
        Returns:
            True if initialization succeeded
        """
        try:
            # Compute microphone positions
            self._mic_positions = self._compute_mic_positions()
            
            # Pre-compute steering vectors
            self._precompute_steering_vectors()
            
            # Generate beam angles
            self._beam_angles = np.linspace(
                0, 2 * np.pi,
                self.acoustic_config.n_beam_angles,
                endpoint=False
            )
            
            return True
        except Exception as e:
            if self.acoustic_config.enable_numba and not HAS_NUMBA:
                print("Warning: Numba not available, using pure Python")
            return False
    
    def _on_shutdown(self) -> None:
        """Shutdown the acoustic plugin."""
        self._mic_positions = None
        self._steering_vectors = None
        self._freq_indices = None
        self._beam_angles = None
    
    def _process_impl(self, data: ShadowData) -> ShadowData:
        """Process acoustic shadow data.
        
        Pipeline:
        1. Extract microphone signals from raw data
        2. Compute STFT for each microphone
        3. Beamform to find shadow directions
        4. Detect shadow regions from power minima
        5. Reconstruct contour from shadow angles
        
        Args:
            data: Input shadow data with raw microphone signals
            
        Returns:
            Processed shadow data with reconstructed contour
        """
        # Validate input
        if data.raw_data is None or len(data.raw_data.raw_data) == 0:
            data.stage = ProcessingStage.RAW
            return data
        
        # Extract microphone signals
        signals = self._extract_signals(data.raw_data)
        if signals is None:
            data.stage = ProcessingStage.RAW
            return data
        
        # Stage 1: Preprocessing (STFT)
        spectra = self._compute_stft_all_mics(signals)
        data.stage = ProcessingStage.PREPROCESSED
        
        # Stage 2: Beamforming
        beamformer_output = self._beamform(spectra)
        data.stage = ProcessingStage.BEAMFORMED
        
        # Stage 3: Shadow detection
        shadow_angles = self._detect_shadows(beamformer_output)
        data.stage = ProcessingStage.DETECTED
        
        # Stage 4: Contour reconstruction
        if len(shadow_angles) >= 3:
            contour = self._reconstruct_contour(shadow_angles, beamformer_output)
            data.contour = contour
            data.stage = ProcessingStage.RECONSTRUCTED
        
        return data
    
    def _compute_mic_positions(self) -> np.ndarray:
        """Compute 4-microphone array geometry.
        
        Optimal configuration: Square array with 21mm spacing.
        This provides uniform angular resolution and minimal sidelobes.
        
        Returns:
            (n_mics, 2) array of (x, y) microphone positions in meters.
        """
        d = self.acoustic_config.mic_spacing
        return np.array([
            [-d/2, -d/2],  # Mic 0: bottom-left
            [d/2, -d/2],   # Mic 1: bottom-right
            [d/2, d/2],    # Mic 2: top-right
            [-d/2, d/2],   # Mic 3: top-left
        ], dtype=np.float32)
    
    def _precompute_steering_vectors(self) -> None:
        """Precompute steering vectors for all angles.
        
        This is the key to O(1) complexity - all beamforming weights
        are computed once at initialization, not per-frame.
        """
        cfg = self.acoustic_config
        n_angles = cfg.n_beam_angles
        
        # Frequency bins
        freqs = np.fft.rfftfreq(cfg.frame_size, 1.0 / cfg.sample_rate)
        
        # Only use ultrasonic frequencies
        valid_freqs = (freqs >= cfg.frequency_min) & (freqs <= cfg.frequency_max)
        self._freq_indices = np.where(valid_freqs)[0]
        
        angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
        
        # Steering vectors: (n_angles, n_freqs, n_mics)
        self._steering_vectors = np.zeros(
            (n_angles, len(self._freq_indices), cfg.n_mics),
            dtype=np.complex64
        )
        
        for i, angle in enumerate(angles):
            direction = np.array([np.cos(angle), np.sin(angle)])
            k = 2 * np.pi * freqs[self._freq_indices] / SPEED_OF_SOUND
            
            for j, freq_idx in enumerate(self._freq_indices):
                delays = np.dot(self._mic_positions, direction) / SPEED_OF_SOUND
                self._steering_vectors[i, j, :] = np.exp(
                    -1j * 2 * np.pi * freqs[freq_idx] * delays
                )
    
    def _extract_signals(self, raw_data: RawSensorData) -> Optional[np.ndarray]:
        """Extract microphone signals from raw data.
        
        Args:
            raw_data: Raw sensor data container
            
        Returns:
            (n_mics, n_samples) array of microphone signals
        """
        raw = raw_data.raw_data
        
        # Handle different input formats
        if raw.ndim == 1:
            # Single channel - reshape
            n_samples = len(raw) // self.acoustic_config.n_mics
            if n_samples * self.acoustic_config.n_mics != len(raw):
                return None
            signals = raw[:n_samples * self.acoustic_config.n_mics].reshape(
                self.acoustic_config.n_mics, n_samples
            )
        elif raw.ndim == 2:
            # Already (n_mics, n_samples)
            if raw.shape[0] != self.acoustic_config.n_mics:
                # Try transposing
                if raw.shape[1] == self.acoustic_config.n_mics:
                    signals = raw.T
                else:
                    return None
            else:
                signals = raw
        else:
            return None
        
        return signals.astype(np.float32)
    
    def _compute_stft_all_mics(
        self,
        signals: np.ndarray
    ) -> np.ndarray:
        """Compute STFT for all microphones.
        
        Args:
            signals: (n_mics, n_samples) microphone signals
            
        Returns:
            (n_mics, n_freqs, n_frames) STFT spectra
        """
        cfg = self.acoustic_config
        n_mics, n_samples = signals.shape
        
        if HAS_SCIPY:
            spectra = []
            for i in range(n_mics):
                f, t, Zxx = signal.stft(
                    signals[i],
                    fs=cfg.sample_rate,
                    nperseg=cfg.frame_size,
                    noverlap=cfg.hop_size,
                    boundary='constant'
                )
                spectra.append(Zxx)
            return np.array(spectra, dtype=np.complex64)
        else:
            # Simple FFT-based STFT fallback
            hop = cfg.hop_size
            n_frames = (n_samples - cfg.frame_size) // hop + 1
            n_freqs = len(np.fft.rfftfreq(cfg.frame_size))
            
            spectra = np.zeros((n_mics, n_freqs, n_frames), dtype=np.complex64)
            for i in range(n_mics):
                for j in range(n_frames):
                    start = j * hop
                    frame = signals[i, start:start + cfg.frame_size]
                    if len(frame) == cfg.frame_size:
                        spectra[i, :, j] = np.fft.rfft(frame)
            
            return spectra
    
    def _beamform(self, spectra: np.ndarray) -> np.ndarray:
        """Perform delay-and-sum beamforming.
        
        Args:
            spectra: (n_mics, n_freqs, n_frames) STFT spectra
            
        Returns:
            (n_angles,) beamformer output power
        """
        # Average over time frames
        avg_spectrum = np.mean(spectra, axis=2)  # (n_mics, n_freqs)
        
        # Extract only valid frequency bins
        valid_spectrum = avg_spectrum[:, self._freq_indices]  # (n_mics, n_valid_freqs)
        
        # Use numba-optimized or pure Python beamforming
        if HAS_NUMBA and self.acoustic_config.enable_numba:
            return self._beamform_numba(
                valid_spectrum,
                self._steering_vectors,
                self._freq_indices
            )
        else:
            return self._beamform_python(
                valid_spectrum,
                self._steering_vectors
            )
    
    @staticmethod
    @jit(nopython=True, parallel=True, fastmath=True, cache=True)
    def _beamform_numba(
        signals: np.ndarray,
        steering_vectors: np.ndarray,
        freq_indices: np.ndarray
    ) -> np.ndarray:
        """Numba-optimized delay-and-sum beamforming - O(1) per angle.
        
        Args:
            signals: (n_mics, n_freqs) FFT of microphone signals
            steering_vectors: Precomputed steering vectors (n_angles, n_freqs, n_mics)
            freq_indices: Indices of valid frequencies
            
        Returns:
            (n_angles,) beamformer output power
        """
        n_angles = steering_vectors.shape[0]
        n_freqs = len(freq_indices)
        n_mics = signals.shape[0]
        
        output = np.zeros(n_angles, dtype=np.float32)
        
        for i in prange(n_angles):
            power = 0.0
            for j in range(n_freqs):
                beamformed = np.complex64(0.0)
                for m in range(n_mics):
                    beamformed += signals[m, j] * np.conj(steering_vectors[i, j, m])
                power += np.abs(beamformed) ** 2
            output[i] = power / n_freqs
        
        return output
    
    def _beamform_python(
        self,
        signals: np.ndarray,
        steering_vectors: np.ndarray
    ) -> np.ndarray:
        """Pure Python beamforming (fallback when numba unavailable).
        
        Args:
            signals: (n_mics, n_freqs) FFT of microphone signals
            steering_vectors: Precomputed steering vectors
            
        Returns:
            (n_angles,) beamformer output power
        """
        n_angles = steering_vectors.shape[0]
        n_freqs = signals.shape[1]
        
        output = np.zeros(n_angles, dtype=np.float32)
        
        for i in range(n_angles):
            power = 0.0
            for j in range(n_freqs):
                beamformed = np.complex64(0.0)
                for m in range(signals.shape[0]):
                    beamformed += signals[m, j] * np.conj(steering_vectors[i, j, m])
                power += np.abs(beamformed) ** 2
            output[i] = power / n_freqs
        
        return output
    
    def _detect_shadows(self, beamformer_output: np.ndarray) -> np.ndarray:
        """Detect shadow regions from beamformer output.
        
        Shadows appear as regions of significantly reduced power.
        We use adaptive thresholding based on the power distribution.
        
        Args:
            beamformer_output: (n_angles,) beamformer power
            
        Returns:
            Array of angles where shadows are detected
        """
        cfg = self.acoustic_config
        
        # Convert to dB
        power_db = 10 * np.log10(beamformer_output + 1e-10)
        
        # Adaptive threshold: shadows are below mean - 2*std
        threshold = np.mean(power_db) - 2 * np.std(power_db)
        threshold = max(threshold, cfg.threshold_db)
        
        # Find shadow regions
        shadow_mask = power_db < threshold
        
        return self._beam_angles[shadow_mask]
    
    def _reconstruct_contour(
        self,
        shadow_angles: np.ndarray,
        beamformer_output: np.ndarray
    ) -> ShadowContour:
        """Reconstruct shadow contour from detected shadow angles.
        
        Args:
            shadow_angles: Angles where shadows were detected
            beamformer_output: Beamformer output for confidence calculation
            
        Returns:
            Reconstructed shadow contour
        """
        # Sort angles for proper contour ordering
        sorted_angles = np.sort(shadow_angles)
        
        # Estimate distance based on shadow width
        # Simplified: use fixed typical hand distance
        estimated_radius = 0.15  # 15cm typical hand distance
        
        # Convert to 3D Cartesian coordinates (z=0 for 2D array)
        x = estimated_radius * np.cos(sorted_angles)
        y = estimated_radius * np.sin(sorted_angles)
        z = np.zeros_like(x)
        
        points = np.column_stack([x, y, z]).astype(np.float32)
        
        # Compute centroid
        centroid = compute_centroid(points)
        
        # Compute confidence based on power contrast
        power_normalized = beamformer_output / np.max(beamformer_output)
        confidence = 1.0 - np.interp(
            np.linspace(0, len(power_normalized), len(points)),
            np.arange(len(power_normalized)),
            power_normalized
        )
        confidence = np.clip(confidence, 0.0, 1.0).astype(np.float32)
        
        # Compute area
        area = estimate_surface_area(points)
        
        return ShadowContour(
            points=points,
            confidence=confidence,
            centroid=centroid,
            area=area,
            normal=Vector3D(0, 0, 1),  # Array normal
            timestamp=Timestamp(),
            quality=ShadowQuality.GOOD  # Will be auto-computed
        )
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        info = super().get_info()
        info.update({
            'sample_rate': self.acoustic_config.sample_rate,
            'n_mics': self.acoustic_config.n_mics,
            'mic_spacing_mm': self.acoustic_config.mic_spacing * 1000,
            'frequency_range_hz': [
                self.acoustic_config.frequency_min,
                self.acoustic_config.frequency_max
            ],
            'has_numba': HAS_NUMBA,
            'has_scipy': HAS_SCIPY
        })
        return info


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_default_acoustic_plugin() -> AcousticPlugin:
    """Create a default-configured acoustic plugin.
    
    Returns:
        Initialized acoustic plugin instance
    """
    config = AcousticConfig(
        name="acoustic_default",
        enabled=True,
        priority=10
    )
    plugin = AcousticPlugin(config)
    return plugin


def benchmark_acoustic_plugin(
    n_iterations: int = 1000,
    n_samples: int = 2048
) -> Dict[str, float]:
    """Benchmark acoustic plugin performance.
    
    Args:
        n_iterations: Number of benchmark iterations
        n_samples: Number of samples per microphone
        
    Returns:
        Dictionary with timing statistics
    """
    # Create plugin
    plugin = create_default_acoustic_plugin()
    plugin.initialize()
    
    # Generate test signals
    signals = np.random.randn(4, n_samples).astype(np.float32)
    raw_data = RawSensorData(
        sensor_type=SensorType.ACOUSTIC,
        raw_data=signals,
        sample_rate=96000
    )
    data = ShadowData(raw_data=raw_data)
    
    # Warm-up
    for _ in range(10):
        plugin.process(data.copy())
    
    # Benchmark
    times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        plugin.process(data.copy())
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    
    plugin.shutdown()
    
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
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Acoustic Shadow Plugin - Benchmark")
    print("=" * 60)
    
    # Run benchmark
    results = benchmark_acoustic_plugin(n_iterations=1000)
    
    print(f"\nPerformance Results:")
    print(f"  Mean latency: {results['mean_ms']:.3f} ms")
    print(f"  Std dev: {results['std_ms']:.3f} ms")
    print(f"  P99 latency: {results['p99_ms']:.3f} ms")
    print(f"  Throughput: {results['throughput_fps']:.0f} fps")
    
    target_latency = 10.0  # ms
    if results['p99_ms'] < target_latency:
        print(f"\n✓ Target met: P99 < {target_latency}ms")
    else:
        print(f"\n✗ Target missed: P99 = {results['p99_ms']:.2f}ms")
    
    print("=" * 60)
