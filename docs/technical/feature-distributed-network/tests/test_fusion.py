"""
Tests for Shadow Fusion and Global Map.
"""

import asyncio
import pytest
import math
import time
from typing import List

from fusion.shadow_fusion import (
    Vector2D, ArrayPosition, ShadowObservation, ShadowFusionEngine,
    SpatialHash, TriangulationFusion, FusedShadow
)
from fusion.global_map import (
    GlobalObject, GlobalShadowMap, ArrayCoverage, CoveragePlanner
)


class TestVector2D:
    """Test Vector2D class."""
    
    def test_creation(self):
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
    
    def test_addition(self):
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_subtraction(self):
        v1 = Vector2D(5.0, 5.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 2.0
    
    def test_scalar_multiplication(self):
        v = Vector2D(2.0, 3.0)
        result = v * 2.0
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_magnitude(self):
        v = Vector2D(3.0, 4.0)
        assert v.magnitude() == 5.0
    
    def test_distance(self):
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_to(v2) == 5.0
    
    def test_to_tuple(self):
        v = Vector2D(1.5, 2.5)
        assert v.to_tuple() == (1.5, 2.5)


class TestArrayPosition:
    """Test ArrayPosition class."""
    
    def test_local_to_global(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(10.0, 10.0),
            orientation=0.0
        )
        
        local = Vector2D(3.0, 4.0)
        global_pos = pos.local_to_global(local)
        
        # With 0 orientation, just add
        assert global_pos.x == 13.0
        assert global_pos.y == 14.0
    
    def test_local_to_global_with_rotation(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(0.0, 0.0),
            orientation=90.0  # 90 degrees
        )
        
        local = Vector2D(1.0, 0.0)
        global_pos = pos.local_to_global(local)
        
        # Rotated 90 degrees, x becomes y
        assert abs(global_pos.x - 0.0) < 0.001
        assert abs(global_pos.y - 1.0) < 0.001
    
    def test_global_to_local(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(10.0, 10.0),
            orientation=0.0
        )
        
        global_pos = Vector2D(13.0, 14.0)
        local = pos.global_to_local(global_pos)
        
        assert local.x == 3.0
        assert local.y == 4.0


class TestSpatialHash:
    """Test SpatialHash class."""
    
    @pytest.mark.asyncio
    async def test_insert_and_query(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.5, 0.5))
        
        # Query near the object
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" in neighbors
    
    @pytest.mark.asyncio
    async def test_query_excludes_distant(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj2", Vector2D(10.0, 10.0))
        
        # Query near obj1
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 2.0)
        assert "obj1" in neighbors
        assert "obj2" not in neighbors
    
    @pytest.mark.asyncio
    async def test_update_position(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj1", Vector2D(5.0, 5.0))  # Update
        
        neighbors = await sh.query_neighbors(Vector2D(5.0, 5.0), 1.0)
        assert "obj1" in neighbors
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" not in neighbors
    
    @pytest.mark.asyncio
    async def test_remove(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.remove("obj1")
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" not in neighbors
    
    @pytest.mark.asyncio
    async def test_clear(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj2", Vector2D(1.0, 1.0))
        await sh.clear()
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 10.0)
        assert len(neighbors) == 0


class TestShadowFusionEngine:
    """Test ShadowFusionEngine class."""
    
    @pytest.mark.asyncio
    async def test_single_observation_creates_shadow(self):
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        assert fused is not None
        assert fused.observation_count == 1
        assert "array1" in fused.contributing_arrays
    
    @pytest.mark.asyncio
    async def test_nearby_observations_fuse(self):
        engine = ShadowFusionEngine(fusion_radius=1.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs1 = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        obs2 = ShadowObservation(
            observation_id="obs2",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.1, 0.0),  # Very close
            confidence=0.7,
            angle=0.0,
            distance=5.1
        )
        
        fused1 = await engine.process_observation(obs1)
        fused2 = await engine.process_observation(obs2)
        
        # Should be same shadow
        assert fused1.shadow_id == fused2.shadow_id
        assert fused2.observation_count == 2
    
    @pytest.mark.asyncio
    async def test_distant_observations_create_separate(self):
        engine = ShadowFusionEngine(fusion_radius=1.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs1 = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        obs2 = ShadowObservation(
            observation_id="obs2",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(15.0, 0.0),  # Far away
            confidence=0.7,
            angle=0.0,
            distance=15.0
        )
        
        fused1 = await engine.process_observation(obs1)
        fused2 = await engine.process_observation(obs2)
        
        # Should be different shadows
        assert fused1.shadow_id != fused2.shadow_id
    
    @pytest.mark.asyncio
    async def test_low_confidence_rejected(self):
        engine = ShadowFusionEngine(min_confidence=0.5)
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.3,  # Below threshold
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        assert fused is None
    
    @pytest.mark.asyncio
    async def test_fusion_callback(self):
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        callbacks = []
        def on_fuse(fused):
            callbacks.append(fused)
        
        engine.add_fusion_callback(on_fuse)
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        await engine.process_observation(obs)
        
        assert len(callbacks) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_shadows(self):
        engine = ShadowFusionEngine(max_shadow_age_ms=100.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        # Wait for shadow to become stale
        await asyncio.sleep(0.15)
        
        stale = await engine.cleanup_stale_shadows(time.time_ns())
        
        assert len(stale) == 1
        assert engine.get_shadow_count() == 0


class TestTriangulationFusion:
    """Test TriangulationFusion class."""
    
    def test_triangulation_with_three_arrays(self):
        tri = TriangulationFusion(min_arrays_for_triangulation=3)
        
        observations = [
            ShadowObservation("obs1", "array1", 0, Vector2D(0.0, 0.0), 0.9, 45.0, 5.0),
            ShadowObservation("obs2", "array2", 0, Vector2D(10.0, 0.0), 0.9, 135.0, 5.0),
            ShadowObservation("obs3", "array3", 0, Vector2D(5.0, 8.66), 0.9, 270.0, 5.0),
        ]
        
        result = tri.triangulate(observations)
        
        assert result is not None
        position, confidence = result
        assert confidence > 0.5
    
    def test_triangulation_insufficient_arrays(self):
        tri = TriangulationFusion(min_arrays_for_triangulation=3)
        
        observations = [
            ShadowObservation("obs1", "array1", 0, Vector2D(0.0, 0.0), 0.9, 45.0, 5.0),
            ShadowObservation("obs2", "array2", 0, Vector2D(10.0, 0.0), 0.9, 135.0, 5.0),
        ]
        
        result = tri.triangulate(observations)
        
        assert result is None
    
    def test_bearing_intersection(self):
        tri = TriangulationFusion()
        
        # Two arrays at right angles should intersect at (5, 5)
        intersection = tri.calculate_bearing_intersection(
            Vector2D(0.0, 0.0), 45.0,   # From origin at 45 degrees
            Vector2D(10.0, 0.0), 135.0  # From (10, 0) at 135 degrees
        )
        
        assert intersection is not None
        assert abs(intersection.x - 5.0) < 0.1
        assert abs(intersection.y - 5.0) < 0.1


class TestGlobalObject:
    """Test GlobalObject class."""
    
    def test_update_position(self):
        obj = GlobalObject(
            object_id="obj1",
            created_ns=time.time_ns(),
            position=Vector2D(0.0, 0.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            primary_array="array1",
            visible_arrays={"array1"},
            last_seen_ns=time.time_ns()
        )
        
        obj.update_position(Vector2D(1.0, 0.0), time.time_ns() + 100_000_000)
        
        assert obj.position.x == 1.0
        assert obj.velocity.x > 0  # Should have positive velocity
    
    def test_predict_position(self):
        obj = GlobalObject(
            object_id="obj1",
            created_ns=time.time_ns(),
            position=Vector2D(0.0, 0.0),
            velocity=Vector2D(1.0, 0.0),  # 1 m/s in x
            confidence=0.8,
            primary_array="array1",
            visible_arrays={"array1"},
            last_seen_ns=time.time_ns()
        )
        
        future_time = time.time_ns() + 1_000_000_000  # 1 second later
        predicted = obj.predict_position(future_time)
        
        assert abs(predicted.x - 1.0) < 0.1


class TestGlobalShadowMap:
    """Test GlobalShadowMap class."""
    
    @pytest.mark.asyncio
    async def test_update_from_fusion_creates_object(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        obj = await gmap.update_from_fusion(fused)
        
        assert obj is not None
        assert obj.object_id.startswith("obj_")
    
    @pytest.mark.asyncio
    async def test_object_callback(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        events = []
        def on_event(obj, event):
            events.append((obj, event))
        
        gmap.add_object_callback(on_event)
        
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        await gmap.update_from_fusion(fused)
        
        assert len(events) == 1
        assert events[0][1] == "created"
    
    @pytest.mark.asyncio
    async def test_get_objects_in_region(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        # Create object at (5, 5)
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        await gmap.update_from_fusion(fused)
        
        # Query region containing the object
        objects = gmap.get_objects_in_region(Vector2D(0.0, 0.0), 10.0)
        assert len(objects) == 1
        
        # Query region not containing the object
        objects = gmap.get_objects_in_region(Vector2D(20.0, 20.0), 2.0)
        assert len(objects) == 0


class TestCoveragePlanner:
    """Test CoveragePlanner class."""
    
    def test_single_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(1, 5.0)
        
        assert len(positions) == 1
        assert positions[0] == (10.0, 10.0)  # Center
    
    def test_four_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(4, 5.0)
        
        assert len(positions) == 4
        # Should be near corners
    
    def test_eight_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(8, 5.0)
        
        assert len(positions) == 8
    
    def test_coverage_estimation(self):
        planner = CoveragePlanner((10.0, 10.0))
        positions = [(5.0, 5.0)]  # Single center array
        
        coverage = planner.estimate_coverage(positions, 10.0)
        
        # Single array with 10m radius should cover most of 10x10 room
        assert coverage > 0.7


class TestFusionPerformance:
    """Performance tests for fusion."""
    
    @pytest.mark.asyncio
    async def test_fusion_throughput(self):
        """Test fusion processing throughput."""
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        # Create many observations
        observations = []
        for i in range(100):
            obs = ShadowObservation(
                observation_id=f"obs_{i}",
                array_id="array1",
                timestamp_ns=time.time_ns() + i * 1_000_000,
                global_position=Vector2D(float(i) * 0.5, 0.0),
                confidence=0.8,
                angle=0.0,
                distance=float(i) * 0.5
            )
            observations.append(obs)
        
        # Process all
        start = time.time()
        await engine.process_observations(observations)
        elapsed = time.time() - start
        
        # Should process 100 observations quickly
        assert elapsed < 1.0
    
    def test_spatial_hash_performance(self):
        """Test spatial hash query performance."""
        import timeit
        
        async def benchmark():
            sh = SpatialHash(cell_size=1.0)
            
            # Insert 1000 objects
            for i in range(1000):
                await sh.insert(f"obj_{i}", Vector2D(float(i % 100), float(i // 100)))
            
            # Time queries
            start = time.time()
            for _ in range(100):
                await sh.query_neighbors(Vector2D(50.0, 50.0), 5.0)
            elapsed = time.time() - start
            
            return elapsed
        
        elapsed = asyncio.run(benchmark())
        
        # 100 queries should be fast
        assert elapsed < 0.1
