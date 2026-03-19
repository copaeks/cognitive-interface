"""
Multi-Array Shadow Fusion Algorithms.

Fuses shadow data from multiple microphone arrays to create unified tracking.
Implements O(1) per object complexity using spatial hashing and efficient
conflict resolution.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Iterator
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Vector2D:
    """2D vector for spatial calculations."""
    x: float
    y: float
    
    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def distance_to(self, other: Vector2D) -> float:
        return (self - other).magnitude()
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass(slots=True)
class ArrayPosition:
    """Position and orientation of a microphone array."""
    array_id: str
    position: Vector2D
    orientation: float  # Degrees from North
    
    def local_to_global(self, local_pos: Vector2D) -> Vector2D:
        """Convert local array coordinates to global."""
        # Rotate by orientation
        rad = math.radians(self.orientation)
        cos_o = math.cos(rad)
        sin_o = math.sin(rad)
        
        rotated = Vector2D(
            local_pos.x * cos_o - local_pos.y * sin_o,
            local_pos.x * sin_o + local_pos.y * cos_o
        )
        
        # Translate to array position
        return self.position + rotated
    
    def global_to_local(self, global_pos: Vector2D) -> Vector2D:
        """Convert global coordinates to local array coordinates."""
        # Translate relative to array
        relative = global_pos - self.position
        
        # Rotate by negative orientation
        rad = math.radians(-self.orientation)
        cos_o = math.cos(rad)
        sin_o = math.sin(rad)
        
        return Vector2D(
            relative.x * cos_o - relative.y * sin_o,
            relative.x * sin_o + relative.y * cos_o
        )


@dataclass(slots=True)
class ShadowObservation:
    """Single shadow observation from an array."""
    observation_id: str
    array_id: str
    timestamp_ns: int
    global_position: Vector2D
    confidence: float  # 0-1
    angle: float  # Angle from array
    distance: float  # Distance from array
    
    def __hash__(self) -> int:
        return hash(self.observation_id)


@dataclass(slots=True)
class FusedShadow:
    """Fused shadow from multiple observations."""
    shadow_id: str
    timestamp_ns: int
    position: Vector2D
    velocity: Vector2D
    confidence: float
    contributing_arrays: Set[str]
    observation_count: int
    last_update_ns: int
    
    @property
    def age_ms(self) -> float:
        """Age of shadow in milliseconds."""
        return 0.0  # Calculated externally with current time


class SpatialHash:
    """
    Spatial hashing for O(1) shadow lookup.
    
    Divides space into grid cells for efficient neighbor queries.
    """
    
    def __init__(self, cell_size: float = 1.0) -> None:
        self.cell_size = cell_size
        self._grid: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        self._positions: Dict[str, Vector2D] = {}
        self._lock = asyncio.Lock()
    
    def _get_cell(self, position: Vector2D) -> Tuple[int, int]:
        """Get grid cell for position."""
        return (
            int(position.x / self.cell_size),
            int(position.y / self.cell_size)
        )
    
    def _get_neighbor_cells(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get cell and all 8 neighbors."""
        x, y = cell
        return [
            (x, y), (x+1, y), (x-1, y),
            (x, y+1), (x, y-1),
            (x+1, y+1), (x+1, y-1),
            (x-1, y+1), (x-1, y-1)
        ]
    
    async def insert(self, obj_id: str, position: Vector2D) -> None:
        """Insert object into spatial hash."""
        async with self._lock:
            # Remove from old cell if exists
            if obj_id in self._positions:
                old_cell = self._get_cell(self._positions[obj_id])
                self._grid[old_cell].discard(obj_id)
            
            # Insert into new cell
            cell = self._get_cell(position)
            self._grid[cell].add(obj_id)
            self._positions[obj_id] = position
    
    async def remove(self, obj_id: str) -> None:
        """Remove object from spatial hash."""
        async with self._lock:
            if obj_id in self._positions:
                cell = self._get_cell(self._positions[obj_id])
                self._grid[cell].discard(obj_id)
                del self._positions[obj_id]
    
    async def query_neighbors(
        self,
        position: Vector2D,
        radius: float
    ) -> Set[str]:
        """Query objects within radius (O(1) average)."""
        async with self._lock:
            center_cell = self._get_cell(position)
            
            # Determine cell range to check based on radius
            cells_to_check = radius / self.cell_size
            if cells_to_check <= 1.0:
                cells = self._get_neighbor_cells(center_cell)
            else:
                # Expand search for larger radii
                cells = []
                range_int = int(cells_to_check) + 1
                for dx in range(-range_int, range_int + 1):
                    for dy in range(-range_int, range_int + 1):
                        cells.append((center_cell[0] + dx, center_cell[1] + dy))
            
            # Collect candidates
            candidates: Set[str] = set()
            for cell in cells:
                candidates.update(self._grid.get(cell, set()))
            
            # Filter by actual distance
            result: Set[str] = set()
            for obj_id in candidates:
                if obj_id in self._positions:
                    dist = position.distance_to(self._positions[obj_id])
                    if dist <= radius:
                        result.add(obj_id)
            
            return result
    
    async def get_position(self, obj_id: str) -> Optional[Vector2D]:
        """Get position of object."""
        async with self._lock:
            return self._positions.get(obj_id)
    
    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._grid.clear()
            self._positions.clear()


class ShadowFusionEngine:
    """
    Multi-array shadow fusion engine.
    
    Fuses observations from multiple arrays into unified shadow tracks.
    Maintains O(1) per object complexity using spatial hashing.
    """
    
    def __init__(
        self,
        fusion_radius: float = 0.5,  # Meters
        min_confidence: float = 0.3,
        max_shadow_age_ms: float = 500.0,
        spatial_cell_size: float = 1.0
    ) -> None:
        self.fusion_radius = fusion_radius
        self.min_confidence = min_confidence
        self.max_shadow_age_ms = max_shadow_age_ms
        
        # Array positions (known from calibration)
        self._array_positions: Dict[str, ArrayPosition] = {}
        
        # Fused shadows
        self._shadows: Dict[str, FusedShadow] = {}
        self._spatial_hash = SpatialHash(spatial_cell_size)
        
        # Observation to shadow mapping
        self._observation_map: Dict[str, str] = {}  # observation_id -> shadow_id
        
        # Statistics
        self._fusion_count = 0
        self._conflict_count = 0
        
        # Callbacks
        self._fusion_callbacks: List[Callable[[FusedShadow], None]] = []
        self._lock = asyncio.Lock()
        
        # Shadow ID counter
        self._shadow_counter = 0
    
    def register_array(self, position: ArrayPosition) -> None:
        """Register array position for coordinate transformation."""
        self._array_positions[position.array_id] = position
    
    def unregister_array(self, array_id: str) -> None:
        """Unregister array."""
        if array_id in self._array_positions:
            del self._array_positions[array_id]
    
    def add_fusion_callback(self, callback: Callable[[FusedShadow], None]) -> None:
        """Add callback for new fused shadows."""
        self._fusion_callbacks.append(callback)
    
    async def process_observation(self, obs: ShadowObservation) -> Optional[FusedShadow]:
        """
        Process a new shadow observation.
        
        O(1) complexity per observation using spatial hashing.
        """
        if obs.confidence < self.min_confidence:
            return None
        
        async with self._lock:
            # Check if observation already mapped
            if obs.observation_id in self._observation_map:
                shadow_id = self._observation_map[obs.observation_id]
                return await self._update_shadow(shadow_id, obs)
            
            # Find nearby shadows for fusion
            nearby = await self._spatial_hash.query_neighbors(
                obs.global_position, self.fusion_radius
            )
            
            if nearby:
                # Fuse with existing shadow
                shadow_id = self._select_best_match(obs, nearby)
                if shadow_id:
                    return await self._fuse_observation(shadow_id, obs)
            
            # Create new shadow
            return await self._create_new_shadow(obs)
    
    async def process_observations(
        self,
        observations: List[ShadowObservation]
    ) -> List[FusedShadow]:
        """Process multiple observations efficiently."""
        results = await asyncio.gather(
            *[self.process_observation(obs) for obs in observations]
        )
        return [r for r in results if r is not None]
    
    async def _select_best_match(
        self,
        obs: ShadowObservation,
        candidates: Set[str]
    ) -> Optional[str]:
        """Select best matching shadow for observation."""
        best_id = None
        best_score = float('inf')
        
        for shadow_id in candidates:
            shadow = self._shadows.get(shadow_id)
            if not shadow:
                continue
            
            # Calculate match score (distance weighted by confidence)
            dist = obs.global_position.distance_to(shadow.position)
            score = dist / (obs.confidence * shadow.confidence + 0.001)
            
            # Prefer shadows from different arrays (better triangulation)
            if obs.array_id not in shadow.contributing_arrays:
                score *= 0.8
            
            if score < best_score:
                best_score = score
                best_id = shadow_id
        
        return best_id
    
    async def _fuse_observation(
        self,
        shadow_id: str,
        obs: ShadowObservation
    ) -> FusedShadow:
        """Fuse observation into existing shadow."""
        shadow = self._shadows[shadow_id]
        
        # Check for conflicts (same array, different observation)
        conflict_resolved = await self._resolve_conflicts(shadow, obs)
        if not conflict_resolved:
            self._conflict_count += 1
            # Create separate shadow instead
            return await self._create_new_shadow(obs)
        
        # Weighted position update
        old_weight = shadow.confidence
        new_weight = obs.confidence
        total_weight = old_weight + new_weight
        
        new_x = (shadow.position.x * old_weight + obs.global_position.x * new_weight) / total_weight
        new_y = (shadow.position.y * old_weight + obs.global_position.y * new_weight) / total_weight
        
        # Update velocity
        dt_ns = obs.timestamp_ns - shadow.last_update_ns
        if dt_ns > 0:
            dt_s = dt_ns / 1_000_000_000
            vx = (new_x - shadow.position.x) / dt_s
            vy = (new_y - shadow.position.y) / dt_s
            # Smooth velocity
            alpha = 0.3
            shadow.velocity = Vector2D(
                shadow.velocity.x * (1 - alpha) + vx * alpha,
                shadow.velocity.y * (1 - alpha) + vy * alpha
            )
        
        # Update shadow
        shadow.position = Vector2D(new_x, new_y)
        shadow.confidence = min(1.0, total_weight * 0.5)  # Cap at 1.0
        shadow.contributing_arrays.add(obs.array_id)
        shadow.observation_count += 1
        shadow.last_update_ns = obs.timestamp_ns
        
        # Update spatial hash
        await self._spatial_hash.insert(shadow_id, shadow.position)
        
        # Map observation
        self._observation_map[obs.observation_id] = shadow_id
        
        self._fusion_count += 1
        
        # Notify callbacks
        for callback in self._fusion_callbacks:
            try:
                callback(shadow)
            except Exception as e:
                logger.error(f"Fusion callback error: {e}")
        
        return shadow
    
    async def _resolve_conflicts(
        self,
        shadow: FusedShadow,
        new_obs: ShadowObservation
    ) -> bool:
        """
        Resolve conflicts when same array reports multiple observations.
        
        Returns True if fusion should proceed, False to create new shadow.
        """
        # If same array already contributed, check if this is an update
        if new_obs.array_id in shadow.contributing_arrays:
            # Check if positions are consistent
            dist = new_obs.global_position.distance_to(shadow.position)
            
            # If very close, treat as update
            if dist < self.fusion_radius * 0.5:
                return True
            
            # If far, might be different object - check confidence
            if new_obs.confidence > shadow.confidence * 1.5:
                # New observation much more confident, replace
                shadow.contributing_arrays.discard(new_obs.array_id)
                return True
            
            # Conflict - don't fuse
            return False
        
        return True
    
    async def _create_new_shadow(self, obs: ShadowObservation) -> FusedShadow:
        """Create new fused shadow from observation."""
        self._shadow_counter += 1
        shadow_id = f"shadow_{self._shadow_counter}"
        
        shadow = FusedShadow(
            shadow_id=shadow_id,
            timestamp_ns=obs.timestamp_ns,
            position=obs.global_position,
            velocity=Vector2D(0.0, 0.0),
            confidence=obs.confidence,
            contributing_arrays={obs.array_id},
            observation_count=1,
            last_update_ns=obs.timestamp_ns
        )
        
        self._shadows[shadow_id] = shadow
        await self._spatial_hash.insert(shadow_id, shadow.position)
        self._observation_map[obs.observation_id] = shadow_id
        
        # Notify callbacks
        for callback in self._fusion_callbacks:
            try:
                callback(shadow)
            except Exception as e:
                logger.error(f"Fusion callback error: {e}")
        
        return shadow
    
    async def _update_shadow(
        self,
        shadow_id: str,
        obs: ShadowObservation
    ) -> Optional[FusedShadow]:
        """Update existing shadow with refined observation."""
        if shadow_id not in self._shadows:
            return None
        
        # Re-fuse with updated observation
        return await self._fuse_observation(shadow_id, obs)
    
    async def cleanup_stale_shadows(self, current_time_ns: int) -> List[str]:
        """Remove shadows that haven't been updated recently."""
        stale_ids = []
        max_age_ns = int(self.max_shadow_age_ms * 1_000_000)
        
        async with self._lock:
            for shadow_id, shadow in list(self._shadows.items()):
                age_ns = current_time_ns - shadow.last_update_ns
                if age_ns > max_age_ns:
                    stale_ids.append(shadow_id)
                    del self._shadows[shadow_id]
                    await self._spatial_hash.remove(shadow_id)
            
            # Clean up observation map
            for obs_id, sid in list(self._observation_map.items()):
                if sid in stale_ids:
                    del self._observation_map[obs_id]
        
        return stale_ids
    
    def get_shadow(self, shadow_id: str) -> Optional[FusedShadow]:
        """Get shadow by ID."""
        return self._shadows.get(shadow_id)
    
    def get_all_shadows(self) -> List[FusedShadow]:
        """Get all active shadows."""
        return list(self._shadows.values())
    
    def get_shadow_count(self) -> int:
        """Get number of active shadows."""
        return len(self._shadows)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get fusion statistics."""
        return {
            "active_shadows": len(self._shadows),
            "fusion_count": self._fusion_count,
            "conflict_count": self._conflict_count,
            "registered_arrays": len(self._array_positions)
        }
    
    async def clear(self) -> None:
        """Clear all shadows and reset state."""
        async with self._lock:
            self._shadows.clear()
            await self._spatial_hash.clear()
            self._observation_map.clear()
            self._fusion_count = 0
            self._conflict_count = 0
            self._shadow_counter = 0


class TriangulationFusion:
    """
    Advanced fusion using triangulation from multiple arrays.
    
    Provides more accurate position estimation when 3+ arrays
    observe the same object.
    """
    
    def __init__(self, min_arrays_for_triangulation: int = 3) -> None:
        self.min_arrays = min_arrays_for_triangulation
    
    def triangulate(
        self,
        observations: List[ShadowObservation]
    ) -> Optional[Tuple[Vector2D, float]]:
        """
        Triangulate position from multiple array observations.
        
        Returns (position, confidence) or None if insufficient data.
        """
        if len(observations) < self.min_arrays:
            return None
        
        # Use least squares for optimal position estimation
        # Each observation gives us: (x - xi)^2 + (y - yi)^2 = di^2
        
        positions = []
        weights = []
        
        for obs in observations:
            positions.append(obs.global_position)
            weights.append(obs.confidence)
        
        # Weighted centroid as initial estimate
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        centroid = Vector2D(0.0, 0.0)
        for pos, w in zip(positions, weights):
            centroid = centroid + pos * (w / total_weight)
        
        # Calculate confidence based on spread
        spread = sum(
            pos.distance_to(centroid) * w
            for pos, w in zip(positions, weights)
        ) / total_weight
        
        confidence = 1.0 / (1.0 + spread)
        
        return centroid, confidence
    
    def calculate_bearing_intersection(
        self,
        array1_pos: Vector2D,
        bearing1: float,
        array2_pos: Vector2D,
        bearing2: float
    ) -> Optional[Vector2D]:
        """
        Calculate intersection of two bearing lines.
        
        Returns intersection point or None if parallel.
        """
        # Convert bearings to unit vectors
        rad1 = math.radians(bearing1)
        rad2 = math.radians(bearing2)
        
        dx1 = math.sin(rad1)
        dy1 = math.cos(rad1)
        dx2 = math.sin(rad2)
        dy2 = math.cos(rad2)
        
        # Line 1: array1_pos + t1 * (dx1, dy1)
        # Line 2: array2_pos + t2 * (dx2, dy2)
        # Solve for intersection
        
        det = dx1 * (-dy2) - dy1 * (-dx2)
        if abs(det) < 1e-10:
            return None  # Parallel lines
        
        diff_x = array2_pos.x - array1_pos.x
        diff_y = array2_pos.y - array1_pos.y
        
        t1 = (diff_x * (-dy2) - diff_y * (-dx2)) / det
        
        return Vector2D(
            array1_pos.x + t1 * dx1,
            array1_pos.y + t1 * dy1
        )
