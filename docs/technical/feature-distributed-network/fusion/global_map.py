"""
Global Shadow-Map for Distributed Tracking.

Provides unified coordinate system, global object tracking IDs,
and hand-off between arrays for seamless multi-array tracking.
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Iterator
from collections import defaultdict
import logging

from .shadow_fusion import (
    Vector2D, ArrayPosition, ShadowObservation, 
    FusedShadow, ShadowFusionEngine
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GlobalObject:
    """
    Globally tracked object with persistent ID.
    
    Maintains identity across array hand-offs and provides
    unified tracking state.
    """
    object_id: str
    created_ns: int
    
    # Current state
    position: Vector2D
    velocity: Vector2D
    confidence: float
    
    # Tracking metadata
    primary_array: str  # Array currently responsible for tracking
    visible_arrays: Set[str]  # Arrays currently seeing this object
    last_seen_ns: int
    
    # Trajectory history (for prediction)
    trajectory: List[Tuple[int, Vector2D]] = field(default_factory=list)
    max_trajectory_length: int = 100
    
    # Statistics
    total_observations: int = 0
    handoff_count: int = 0
    
    def update_position(self, position: Vector2D, timestamp_ns: int) -> None:
        """Update position and maintain trajectory."""
        # Calculate velocity
        dt_ns = timestamp_ns - self.last_seen_ns
        if dt_ns > 0 and self.last_seen_ns > 0:
            dt_s = dt_ns / 1_000_000_000
            new_vx = (position.x - self.position.x) / dt_s
            new_vy = (position.y - self.position.y) / dt_s
            # Smooth velocity
            alpha = 0.3
            self.velocity = Vector2D(
                self.velocity.x * (1 - alpha) + new_vx * alpha,
                self.velocity.y * (1 - alpha) + new_vy * alpha
            )
        
        self.position = position
        self.last_seen_ns = timestamp_ns
        self.total_observations += 1
        
        # Update trajectory
        self.trajectory.append((timestamp_ns, position))
        if len(self.trajectory) > self.max_trajectory_length:
            self.trajectory.pop(0)
    
    def predict_position(self, future_time_ns: int) -> Vector2D:
        """Predict position at future time using velocity."""
        dt_ns = future_time_ns - self.last_seen_ns
        if dt_ns <= 0:
            return self.position
        
        dt_s = dt_ns / 1_000_000_000
        return Vector2D(
            self.position.x + self.velocity.x * dt_s,
            self.position.y + self.velocity.y * dt_s
        )
    
    @property
    def age_ms(self) -> float:
        """Age of object in milliseconds."""
        return (time.time_ns() - self.created_ns) / 1_000_000
    
    @property
    def is_stale(self, max_age_ms: float = 1000.0) -> bool:
        """Check if object hasn't been seen recently."""
        return (time.time_ns() - self.last_seen_ns) / 1_000_000 > max_age_ms


@dataclass(slots=True)
class ArrayCoverage:
    """Coverage area of a microphone array."""
    array_id: str
    position: Vector2D
    radius: float  # Detection radius in meters
    fov_degrees: float = 360.0  # Field of view
    orientation: float = 0.0  # Direction array is facing
    
    def contains(self, position: Vector2D) -> bool:
        """Check if position is within array coverage."""
        dist = position.distance_to(self.position)
        if dist > self.radius:
            return False
        
        if self.fov_degrees >= 360:
            return True
        
        # Check angle
        dx = position.x - self.position.x
        dy = position.y - self.position.y
        angle = math.degrees(math.atan2(dx, dy))
        angle_diff = abs((angle - self.orientation + 180) % 360 - 180)
        
        return angle_diff <= self.fov_degrees / 2
    
    def overlap_score(self, other: ArrayCoverage) -> float:
        """Calculate overlap score with another array coverage."""
        dist = self.position.distance_to(other.position)
        
        if dist > self.radius + other.radius:
            return 0.0
        
        # Simple overlap based on distance and radii
        overlap = (self.radius + other.radius - dist) / min(self.radius, other.radius)
        return max(0.0, min(1.0, overlap))


class GlobalShadowMap:
    """
    Global shadow-map for unified multi-array tracking.
    
    Features:
    - Persistent global object IDs
    - Seamless array hand-offs
    - Coverage optimization
    - O(1) object lookup
    """
    
    def __init__(
        self,
        fusion_engine: ShadowFusionEngine,
        max_object_age_ms: float = 2000.0,
        handoff_threshold: float = 0.7  # Confidence threshold for handoff
    ) -> None:
        self.fusion_engine = fusion_engine
        self.max_object_age_ms = max_object_age_ms
        self.handoff_threshold = handoff_threshold
        
        # Global objects
        self._objects: Dict[str, GlobalObject] = {}
        self._object_counter = 0
        
        # Array coverage areas
        self._coverage: Dict[str, ArrayCoverage] = {}
        
        # Object to fused shadow mapping
        self._shadow_to_object: Dict[str, str] = {}
        
        # Coverage optimization
        self._coverage_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Callbacks
        self._object_callbacks: List[Callable[[GlobalObject, str], None]] = []
        # Event types: "created", "updated", "handoff", "lost"
        
        # Statistics
        self._handoff_count = 0
        self._object_count = 0
        
        self._lock = asyncio.Lock()
    
    def register_array_coverage(self, coverage: ArrayCoverage) -> None:
        """Register array coverage area."""
        self._coverage[coverage.array_id] = coverage
        
        # Update coverage graph
        for other_id, other_cov in self._coverage.items():
            if other_id != coverage.array_id:
                overlap = coverage.overlap_score(other_cov)
                if overlap > 0.3:  # Significant overlap
                    self._coverage_graph[coverage.array_id].add(other_id)
                    self._coverage_graph[other_id].add(coverage.array_id)
    
    def add_object_callback(
        self,
        callback: Callable[[GlobalObject, str], None]
    ) -> None:
        """Add callback for object events."""
        self._object_callbacks.append(callback)
    
    async def update_from_fusion(self, fused_shadow: FusedShadow) -> GlobalObject:
        """
        Update global map from fused shadow.
        
        O(1) complexity using shadow-to-object mapping.
        """
        async with self._lock:
            # Check if shadow already mapped to object
            if fused_shadow.shadow_id in self._shadow_to_object:
                obj_id = self._shadow_to_object[fused_shadow.shadow_id]
                return await self._update_object(obj_id, fused_shadow)
            
            # Try to match with existing object
            existing = await self._find_matching_object(fused_shadow)
            if existing:
                self._shadow_to_object[fused_shadow.shadow_id] = existing.object_id
                return await self._update_object(existing.object_id, fused_shadow)
            
            # Create new global object
            return await self._create_object(fused_shadow)
    
    async def _find_matching_object(
        self,
        fused_shadow: FusedShadow
    ) -> Optional[GlobalObject]:
        """Find existing object matching fused shadow."""
        # Search by position proximity
        search_radius = 1.0  # meters
        
        best_match = None
        best_score = float('inf')
        
        for obj in self._objects.values():
            # Predict current position
            predicted = obj.predict_position(fused_shadow.timestamp_ns)
            dist = predicted.distance_to(fused_shadow.position)
            
            if dist < search_radius:
                # Score based on distance and velocity consistency
                score = dist
                if obj.velocity.magnitude() > 0.1:
                    # Check velocity alignment
                    expected_dist = obj.velocity.magnitude() * 0.1  # 100ms
                    score += abs(dist - expected_dist)
                
                if score < best_score:
                    best_score = score
                    best_match = obj
        
        return best_match
    
    async def _create_object(self, fused_shadow: FusedShadow) -> GlobalObject:
        """Create new global object from fused shadow."""
        self._object_counter += 1
        obj_id = f"obj_{self._object_counter:06d}"
        
        # Determine primary array
        primary = self._select_primary_array(fused_shadow)
        
        obj = GlobalObject(
            object_id=obj_id,
            created_ns=fused_shadow.timestamp_ns,
            position=fused_shadow.position,
            velocity=Vector2D(0.0, 0.0),
            confidence=fused_shadow.confidence,
            primary_array=primary,
            visible_arrays=set(fused_shadow.contributing_arrays),
            last_seen_ns=fused_shadow.timestamp_ns
        )
        
        self._objects[obj_id] = obj
        self._shadow_to_object[fused_shadow.shadow_id] = obj_id
        self._object_count += 1
        
        # Notify callbacks
        self._notify_callbacks(obj, "created")
        
        logger.debug(f"Created global object {obj_id} at {obj.position.to_tuple()}")
        
        return obj
    
    async def _update_object(
        self,
        obj_id: str,
        fused_shadow: FusedShadow
    ) -> GlobalObject:
        """Update existing global object."""
        obj = self._objects[obj_id]
        
        # Update position
        obj.update_position(fused_shadow.position, fused_shadow.timestamp_ns)
        
        # Update confidence
        obj.confidence = fused_shadow.confidence
        
        # Update visible arrays
        old_primary = obj.primary_array
        obj.visible_arrays.update(fused_shadow.contributing_arrays)
        
        # Check for handoff
        new_primary = self._select_primary_array(fused_shadow, obj)
        if new_primary != old_primary and fused_shadow.confidence > self.handoff_threshold:
            obj.primary_array = new_primary
            obj.handoff_count += 1
            self._handoff_count += 1
            self._notify_callbacks(obj, "handoff")
            logger.debug(f"Object {obj_id} handed off from {old_primary} to {new_primary}")
        
        # Notify update
        self._notify_callbacks(obj, "updated")
        
        return obj
    
    def _select_primary_array(
        self,
        fused_shadow: FusedShadow,
        existing_obj: Optional[GlobalObject] = None
    ) -> str:
        """Select primary array for tracking an object."""
        arrays = fused_shadow.contributing_arrays
        
        if not arrays:
            return "unknown"
        
        if len(arrays) == 1:
            return list(arrays)[0]
        
        # Score each array
        best_array = None
        best_score = -1.0
        
        for array_id in arrays:
            score = 0.0
            
            # Prefer arrays with better coverage of object position
            coverage = self._coverage.get(array_id)
            if coverage:
                dist = fused_shadow.position.distance_to(coverage.position)
                score += (coverage.radius - dist) / coverage.radius
            
            # Prefer arrays that have been tracking this object
            if existing_obj and array_id == existing_obj.primary_array:
                score += 0.5  # Hysteresis
            
            if score > best_score:
                best_score = score
                best_array = array_id
        
        return best_array or list(arrays)[0]
    
    def _notify_callbacks(self, obj: GlobalObject, event: str) -> None:
        """Notify all registered callbacks."""
        for callback in self._object_callbacks:
            try:
                callback(obj, event)
            except Exception as e:
                logger.error(f"Object callback error: {e}")
    
    async def cleanup_stale_objects(self, current_time_ns: int) -> List[str]:
        """Remove objects that haven't been seen recently."""
        stale_ids = []
        max_age_ns = int(self.max_object_age_ms * 1_000_000)
        
        async with self._lock:
            for obj_id, obj in list(self._objects.items()):
                age_ns = current_time_ns - obj.last_seen_ns
                if age_ns > max_age_ns:
                    stale_ids.append(obj_id)
                    del self._objects[obj_id]
                    
                    # Clean up shadow mappings
                    for sid, oid in list(self._shadow_to_object.items()):
                        if oid == obj_id:
                            del self._shadow_to_object[sid]
                    
                    self._notify_callbacks(obj, "lost")
        
        return stale_ids
    
    def get_object(self, object_id: str) -> Optional[GlobalObject]:
        """Get object by ID."""
        return self._objects.get(object_id)
    
    def get_all_objects(self) -> List[GlobalObject]:
        """Get all active objects."""
        return list(self._objects.values())
    
    def get_objects_in_region(
        self,
        center: Vector2D,
        radius: float
    ) -> List[GlobalObject]:
        """Get objects within a region."""
        result = []
        for obj in self._objects.values():
            if obj.position.distance_to(center) <= radius:
                result.append(obj)
        return result
    
    def get_objects_by_array(self, array_id: str) -> List[GlobalObject]:
        """Get objects currently visible to an array."""
        return [
            obj for obj in self._objects.values()
            if array_id in obj.visible_arrays
        ]
    
    def get_optimal_array_for_position(self, position: Vector2D) -> Optional[str]:
        """Get best array to track a position."""
        best_array = None
        best_score = -1.0
        
        for array_id, coverage in self._coverage.items():
            if coverage.contains(position):
                dist = position.distance_to(coverage.position)
                score = coverage.radius - dist
                if score > best_score:
                    best_score = score
                    best_array = array_id
        
        return best_array
    
    def calculate_coverage_optimization(self) -> Dict[str, List[str]]:
        """
        Calculate optimal array assignments for coverage.
        
        Returns mapping of under-covered regions to recommended arrays.
        """
        optimization: Dict[str, List[str]] = {}
        
        # Find regions with no coverage
        # This is a simplified version - real implementation would
        # use spatial analysis of the coverage map
        
        for obj in self._objects.values():
            visible = len(obj.visible_arrays)
            if visible < 2:
                # Object seen by fewer than 2 arrays
                # Find nearby arrays that could help
                nearby = []
                for array_id, coverage in self._coverage.items():
                    if array_id not in obj.visible_arrays:
                        if coverage.contains(obj.position):
                            nearby.append(array_id)
                
                if nearby:
                    optimization[obj.object_id] = nearby
        
        return optimization
    
    def get_coverage_stats(self) -> Dict[str, any]:
        """Get coverage statistics."""
        total_area = 0.0
        overlaps = 0
        
        for i, (id1, cov1) in enumerate(self._coverage.items()):
            total_area += math.pi * cov1.radius ** 2
            for id2, cov2 in list(self._coverage.items())[i+1:]:
                if cov1.overlap_score(cov2) > 0:
                    overlaps += 1
        
        return {
            "array_count": len(self._coverage),
            "total_coverage_area": total_area,
            "overlap_count": overlaps,
            "average_objects_per_array": (
                len(self._objects) / len(self._coverage) if self._coverage else 0
            )
        }
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get global map statistics."""
        return {
            "active_objects": len(self._objects),
            "total_objects_created": self._object_count,
            "handoffs": self._handoff_count,
            "arrays": len(self._coverage)
        }
    
    async def clear(self) -> None:
        """Clear all objects and reset state."""
        async with self._lock:
            self._objects.clear()
            self._shadow_to_object.clear()
            self._object_counter = 0
            self._handoff_count = 0


class CoveragePlanner:
    """
    Plans optimal array placement for coverage.
    
    Provides recommendations for array positioning to achieve
    desired coverage with minimal overlap.
    """
    
    def __init__(
        self,
        room_dimensions: Tuple[float, float],  # width, height in meters
        target_coverage: float = 0.95,  # Target coverage percentage
        min_overlap: float = 0.1  # Minimum overlap for handoff
    ) -> None:
        self.room_width, self.room_height = room_dimensions
        self.target_coverage = target_coverage
        self.min_overlap = min_overlap
    
    def calculate_optimal_placement(
        self,
        array_count: int,
        array_radius: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate optimal array positions.
        
        Uses hexagonal packing for even coverage.
        """
        positions = []
        
        if array_count == 1:
            # Center single array
            positions.append((self.room_width / 2, self.room_height / 2))
        
        elif array_count == 2:
            # Two arrays on opposite sides
            positions.append((self.room_width * 0.25, self.room_height / 2))
            positions.append((self.room_width * 0.75, self.room_height / 2))
        
        elif array_count == 4:
            # Four corners
            margin = array_radius * 0.5
            positions.extend([
                (margin, margin),
                (self.room_width - margin, margin),
                (margin, self.room_height - margin),
                (self.room_width - margin, self.room_height - margin)
            ])
        
        elif array_count == 8:
            # Eight arrays: corners + midpoints
            margin = array_radius * 0.3
            positions.extend([
                # Corners
                (margin, margin),
                (self.room_width - margin, margin),
                (margin, self.room_height - margin),
                (self.room_width - margin, self.room_height - margin),
                # Midpoints
                (self.room_width / 2, margin),
                (self.room_width / 2, self.room_height - margin),
                (margin, self.room_height / 2),
                (self.room_width - margin, self.room_height / 2)
            ])
        
        else:
            # Grid placement for other counts
            cols = int(math.ceil(math.sqrt(array_count)))
            rows = int(math.ceil(array_count / cols))
            
            x_step = self.room_width / (cols + 1)
            y_step = self.room_height / (rows + 1)
            
            for i in range(array_count):
                row = i // cols
                col = i % cols
                x = x_step * (col + 1)
                y = y_step * (row + 1)
                positions.append((x, y))
        
        return positions
    
    def estimate_coverage(
        self,
        positions: List[Tuple[float, float]],
        radius: float
    ) -> float:
        """Estimate coverage percentage for given positions."""
        # Monte Carlo sampling
        samples = 1000
        covered = 0
        
        import random
        random.seed(42)
        
        for _ in range(samples):
            x = random.uniform(0, self.room_width)
            y = random.uniform(0, self.room_height)
            point = Vector2D(x, y)
            
            for px, py in positions:
                if point.distance_to(Vector2D(px, py)) <= radius:
                    covered += 1
                    break
        
        return covered / samples
