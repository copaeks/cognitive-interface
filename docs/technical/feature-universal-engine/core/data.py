"""
Universal Shadow Data Structures
================================

Core data types for the Universal Shadow Engine.
Provides platform-agnostic data formats for shadow tracking
across different sensing modalities (acoustic, EM, THz, photoacoustic).

Author: Cognitive AR Empire 2035 Technical Team
Version: 2.0.0
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Tuple, Protocol, runtime_checkable
from enum import Enum, auto
from abc import ABC, abstractmethod
import time


# =============================================================================
# ENUMERATIONS
# =============================================================================

class SensorType(Enum):
    """Enumeration of supported sensor types."""
    ACOUSTIC = auto()
    ELECTROMAGNETIC = auto()
    TERAHERTZ = auto()
    PHOTOACOUSTIC = auto()
    UNKNOWN = auto()


class ShadowQuality(Enum):
    """Quality classification for shadow reconstruction."""
    EXCELLENT = auto()   # > 0.9 confidence
    GOOD = auto()        # 0.7 - 0.9 confidence
    FAIR = auto()        # 0.5 - 0.7 confidence
    POOR = auto()        # 0.3 - 0.5 confidence
    INVALID = auto()     # < 0.3 confidence


class ProcessingStage(Enum):
    """Processing pipeline stages for tracking."""
    RAW = auto()
    PREPROCESSED = auto()
    BEAMFORMED = auto()
    DETECTED = auto()
    RECONSTRUCTED = auto()
    TRACKED = auto()


# =============================================================================
# UNIVERSAL DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True, slots=True)
class Vector3D:
    """Immutable 3D vector for spatial coordinates.
    
    Attributes:
        x: X-coordinate in meters
        y: Y-coordinate in meters
        z: Z-coordinate in meters
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z], dtype=np.float32)
    
    @classmethod
    def from_array(cls, arr: np.ndarray) -> Vector3D:
        """Create from numpy array."""
        if len(arr) >= 3:
            return cls(float(arr[0]), float(arr[1]), float(arr[2]))
        elif len(arr) == 2:
            return cls(float(arr[0]), float(arr[1]), 0.0)
        return cls()
    
    def distance_to(self, other: Vector3D) -> float:
        """Calculate Euclidean distance to another vector."""
        return np.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )


@dataclass(frozen=True, slots=True)
class Timestamp:
    """High-precision timestamp with nanosecond resolution.
    
    Attributes:
        seconds: Unix timestamp in seconds
        nanoseconds: Additional nanoseconds for precision
    """
    seconds: float = field(default_factory=time.time)
    nanoseconds: int = 0
    
    def to_seconds(self) -> float:
        """Convert to total seconds."""
        return self.seconds + self.nanoseconds * 1e-9
    
    def elapsed_since(self, other: Timestamp) -> float:
        """Calculate elapsed time in seconds since another timestamp."""
        return self.to_seconds() - other.to_seconds()


@dataclass(slots=True)
class ShadowContour:
    """Reconstructed shadow contour from any sensing modality.
    
    This is the universal output format for shadow reconstruction
    across all sensor types.
    
    Attributes:
        points: (N, 3) array of 3D contour points in meters
        confidence: (N,) array of confidence values [0, 1]
        centroid: Center of mass of the contour
        area: Estimated surface area in square meters
        normal: Surface normal vector (if available)
        timestamp: When the contour was reconstructed
        quality: Quality classification
    """
    points: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    confidence: np.ndarray = field(default_factory=lambda: np.array([]))
    centroid: Vector3D = field(default_factory=Vector3D)
    area: float = 0.0
    normal: Vector3D = field(default_factory=Vector3D)
    timestamp: Timestamp = field(default_factory=Timestamp)
    quality: ShadowQuality = ShadowQuality.INVALID
    
    def __post_init__(self) -> None:
        """Validate and normalize data after initialization."""
        if len(self.points) > 0:
            if len(self.confidence) == 0:
                self.confidence = np.ones(len(self.points))
            elif len(self.confidence) != len(self.points):
                raise ValueError(
                    f"Confidence length {len(self.confidence)} != "
                    f"points length {len(self.points)}"
                )
            
            # Compute quality from mean confidence
            mean_conf = float(np.mean(self.confidence))
            if mean_conf > 0.9:
                self.quality = ShadowQuality.EXCELLENT
            elif mean_conf > 0.7:
                self.quality = ShadowQuality.GOOD
            elif mean_conf > 0.5:
                self.quality = ShadowQuality.FAIR
            elif mean_conf > 0.3:
                self.quality = ShadowQuality.POOR
            else:
                self.quality = ShadowQuality.INVALID
    
    def is_valid(self) -> bool:
        """Check if contour is valid for tracking."""
        return (
            len(self.points) >= 3 and
            self.quality != ShadowQuality.INVALID and
            self.area > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'points': self.points.tolist(),
            'confidence': self.confidence.tolist(),
            'centroid': [self.centroid.x, self.centroid.y, self.centroid.z],
            'area': self.area,
            'normal': [self.normal.x, self.normal.y, self.normal.z],
            'timestamp': self.timestamp.to_seconds(),
            'quality': self.quality.name
        }


@dataclass(slots=True)
class RawSensorData:
    """Raw sensor data from any modality.
    
    This is the universal input format for all sensor types.
    Each plugin interprets the raw_data field according to its
    sensor specifications.
    
    Attributes:
        sensor_type: Type of sensor that produced this data
        raw_data: Raw sensor readings (plugin-specific format)
        sample_rate: Sampling rate in Hz
        timestamp: When the data was captured
        calibration: Calibration parameters (plugin-specific)
        metadata: Additional plugin-specific metadata
    """
    sensor_type: SensorType = SensorType.UNKNOWN
    raw_data: np.ndarray = field(default_factory=lambda: np.array([]))
    sample_rate: float = 0.0
    timestamp: Timestamp = field(default_factory=Timestamp)
    calibration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate that raw data is non-empty."""
        return len(self.raw_data) > 0 and self.sample_rate > 0


@dataclass(slots=True)
class ShadowData:
    """Universal shadow data container.
    
    This is the primary data structure passed between plugins
    and the core engine. It represents a single frame of
    shadow tracking data.
    
    Attributes:
        frame_id: Unique frame identifier
        sensor_type: Source sensor modality
        raw_data: Raw sensor readings
        contour: Reconstructed shadow contour (if available)
        stage: Current processing stage
        processing_time_ms: Time spent processing this frame
        metadata: Frame-specific metadata
    """
    frame_id: int = 0
    sensor_type: SensorType = SensorType.UNKNOWN
    raw_data: RawSensorData = field(default_factory=RawSensorData)
    contour: Optional[ShadowContour] = None
    stage: ProcessingStage = ProcessingStage.RAW
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def copy(self) -> ShadowData:
        """Create a shallow copy of this data."""
        return ShadowData(
            frame_id=self.frame_id,
            sensor_type=self.sensor_type,
            raw_data=self.raw_data,
            contour=self.contour,
            stage=self.stage,
            processing_time_ms=self.processing_time_ms,
            metadata=self.metadata.copy()
        )


@dataclass(slots=True)
class TrackingResult:
    """Result of hand/object tracking from shadow data.
    
    This is the final output of the shadow tracking pipeline,
    suitable for AR/VR applications.
    
    Attributes:
        tracked: Whether a valid object was detected
        position: 3D position in meters (camera coordinates)
        velocity: 3D velocity in m/s
        orientation: Quaternion or rotation matrix
        confidence: Overall tracking confidence [0, 1]
        contour: Reconstructed contour
        timestamp: When tracking was completed
        latency_ms: End-to-end latency
    """
    tracked: bool = False
    position: Vector3D = field(default_factory=Vector3D)
    velocity: Vector3D = field(default_factory=Vector3D)
    orientation: np.ndarray = field(
        default_factory=lambda: np.eye(3, dtype=np.float32)
    )
    confidence: float = 0.0
    contour: Optional[ShadowContour] = None
    timestamp: Timestamp = field(default_factory=Timestamp)
    latency_ms: float = 0.0
    
    def is_valid(self) -> bool:
        """Check if tracking result is valid."""
        return self.tracked and self.confidence > 0.3


# =============================================================================
# CONFIGURATION DATA STRUCTURES
# =============================================================================

@dataclass(slots=True)
class EngineConfig:
    """Configuration for the Shadow Engine Core.
    
    Attributes:
        max_latency_ms: Maximum allowed processing latency
        enable_parallel: Enable parallel plugin processing
        buffer_size: Frame buffer size for temporal smoothing
        debug_mode: Enable debug logging and diagnostics
    """
    max_latency_ms: float = 10.0
    enable_parallel: bool = True
    buffer_size: int = 5
    debug_mode: bool = False


@dataclass(slots=True)
class PluginConfig:
    """Base configuration for all plugins.
    
    Attributes:
        name: Plugin identifier
        enabled: Whether plugin is active
        priority: Processing priority (higher = earlier)
        parameters: Plugin-specific parameters
    """
    name: str = "unnamed"
    enabled: bool = True
    priority: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PROTOCOLS FOR TYPE CHECKING
# =============================================================================

@runtime_checkable
class DataConvertible(Protocol):
    """Protocol for objects that can convert to/from ShadowData."""
    
    def to_shadow_data(self) -> ShadowData:
        """Convert to universal shadow data format."""
        ...
    
    @classmethod
    def from_shadow_data(cls, data: ShadowData) -> DataConvertible:
        """Create from universal shadow data format."""
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for serializable objects."""
    
    def serialize(self) -> bytes:
        """Serialize to bytes."""
        ...
    
    @classmethod
    def deserialize(cls, data: bytes) -> Serializable:
        """Deserialize from bytes."""
        ...


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compute_bounding_box(points: np.ndarray) -> Tuple[Vector3D, Vector3D]:
    """Compute axis-aligned bounding box from points.
    
    Args:
        points: (N, 3) array of 3D points
        
    Returns:
        Tuple of (min_corner, max_corner) as Vector3D
    """
    if len(points) == 0:
        return Vector3D(), Vector3D()
    
    min_vals = np.min(points, axis=0)
    max_vals = np.max(points, axis=0)
    
    return (
        Vector3D(float(min_vals[0]), float(min_vals[1]), float(min_vals[2])),
        Vector3D(float(max_vals[0]), float(max_vals[1]), float(max_vals[2]))
    )


def compute_centroid(points: np.ndarray) -> Vector3D:
    """Compute centroid of point cloud.
    
    Args:
        points: (N, 3) array of 3D points
        
    Returns:
        Centroid as Vector3D
    """
    if len(points) == 0:
        return Vector3D()
    
    centroid = np.mean(points, axis=0)
    return Vector3D(
        float(centroid[0]),
        float(centroid[1]),
        float(centroid[2]) if len(centroid) > 2 else 0.0
    )


def estimate_surface_area(points: np.ndarray) -> float:
    """Estimate surface area from contour points using convex hull.
    
    Args:
        points: (N, 3) array of contour points
        
    Returns:
        Estimated surface area in square meters
    """
    if len(points) < 3:
        return 0.0
    
    # For 2D contours, use shoelace formula
    if np.all(points[:, 2] == 0) or len(points[0]) == 2:
        x = points[:, 0]
        y = points[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    # For 3D, use projected area
    # Simplified: use area of bounding box faces
    min_corner, max_corner = compute_bounding_box(points)
    dx = max_corner.x - min_corner.x
    dy = max_corner.y - min_corner.y
    dz = max_corner.z - min_corner.z
    
    return 2 * (dx * dy + dy * dz + dz * dx)
