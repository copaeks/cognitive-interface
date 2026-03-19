"""
Unit Tests for Mesh Generation
==============================

Comprehensive test suite for 3D mesh generation from 2D shadows.

Run with: pytest test_mesh_generation.py -v
"""

from __future__ import annotations

import numpy as np
import pytest
from typing import List, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mesh_generator import (
    Mesh3D, MeshConfig, MeshAlgorithm,
    ShadowMeshGenerator, benchmark_mesh_generation
)


class TestMesh3D:
    """Tests for Mesh3D data structure."""
    
    def test_empty_mesh(self):
        """Test creation of empty mesh."""
        mesh = Mesh3D(
            vertices=np.zeros((0, 3), dtype=np.float32),
            faces=np.zeros((0, 3), dtype=np.int32),
            normals=np.zeros((0, 3), dtype=np.float32),
            uvs=np.zeros((0, 2), dtype=np.float32),
        )
        
        assert mesh.n_vertices == 0
        assert mesh.n_faces == 0
        assert mesh.volume == 0.0
        assert mesh.surface_area == 0.0
    
    def test_simple_cube(self):
        """Test mesh properties for a simple cube."""
        # Unit cube vertices
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # Bottom face
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],  # Top face
        ], dtype=np.float32)
        
        # Cube faces (triangulated)
        faces = np.array([
            # Bottom
            [0, 2, 1], [0, 3, 2],
            # Top
            [4, 5, 6], [4, 6, 7],
            # Front
            [0, 1, 5], [0, 5, 4],
            # Back
            [2, 3, 7], [2, 7, 6],
            # Left
            [0, 4, 7], [0, 7, 3],
            # Right
            [1, 2, 6], [1, 6, 5],
        ], dtype=np.int32)
        
        normals = np.zeros_like(vertices)
        uvs = np.zeros((len(vertices), 2), dtype=np.float32)
        
        mesh = Mesh3D(vertices=vertices, faces=faces, normals=normals, uvs=uvs)
        
        assert mesh.n_vertices == 8
        assert mesh.n_faces == 12
        
        # Check bounds
        min_b, max_b = mesh.bounds
        np.testing.assert_array_almost_equal(min_b, [0, 0, 0])
        np.testing.assert_array_almost_equal(max_b, [1, 1, 1])
        
        # Check centroid
        centroid = mesh.centroid
        np.testing.assert_array_almost_equal(centroid, [0.5, 0.5, 0.5])
    
    def test_watertight_check(self):
        """Test watertight detection."""
        # Create watertight tetrahedron
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0.5, 1, 0], [0.5, 0.5, 1]
        ], dtype=np.float32)
        
        faces = np.array([
            [0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]
        ], dtype=np.int32)
        
        normals = np.zeros_like(vertices)
        uvs = np.zeros((len(vertices), 2), dtype=np.float32)
        
        mesh = Mesh3D(vertices=vertices, faces=faces, normals=normals, uvs=uvs)
        
        # Tetrahedron should be watertight
        assert mesh.is_watertight()
    
    def test_non_watertight_mesh(self):
        """Test detection of non-watertight mesh."""
        # Single triangle (not watertight)
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [0.5, 1, 0]
        ], dtype=np.float32)
        
        faces = np.array([[0, 1, 2]], dtype=np.int32)
        normals = np.zeros_like(vertices)
        uvs = np.zeros((len(vertices), 2), dtype=np.float32)
        
        mesh = Mesh3D(vertices=vertices, faces=faces, normals=normals, uvs=uvs)
        
        assert not mesh.is_watertight()


class TestShadowMeshGenerator:
    """Tests for ShadowMeshGenerator."""
    
    @pytest.fixture
    def circular_contour(self):
        """Create a circular test contour."""
        theta = np.linspace(0, 2 * np.pi, 32, endpoint=False)
        radius = 0.05
        return np.column_stack([
            radius * np.cos(theta),
            radius * np.sin(theta)
        ]).astype(np.float32)
    
    @pytest.fixture
    def square_contour(self):
        """Create a square test contour."""
        return np.array([
            [-0.05, -0.05], [0.05, -0.05],
            [0.05, 0.05], [-0.05, 0.05]
        ], dtype=np.float32)
    
    def test_initialization(self):
        """Test generator initialization."""
        config = MeshConfig(algorithm=MeshAlgorithm.EXTRUSION)
        generator = ShadowMeshGenerator(config)
        
        assert generator.config.algorithm == MeshAlgorithm.EXTRUSION
    
    def test_extrusion_generation(self, circular_contour):
        """Test extrusion mesh generation."""
        generator = ShadowMeshGenerator()
        mesh = generator.generate(circular_contour)
        
        assert mesh.n_vertices > 0
        assert mesh.n_faces > 0
        assert len(mesh.normals) == mesh.n_vertices
        assert len(mesh.uvs) == mesh.n_vertices
    
    def test_extrusion_with_confidence(self, circular_contour):
        """Test extrusion with confidence values."""
        generator = ShadowMeshGenerator()
        confidence = np.random.rand(len(circular_contour)).astype(np.float32)
        
        mesh = generator.generate(circular_contour, confidence=confidence)
        
        assert mesh.vertex_colors is not None
        assert len(mesh.vertex_colors) == mesh.n_vertices
    
    def test_different_algorithms(self, circular_contour):
        """Test different mesh generation algorithms."""
        algorithms = [
            MeshAlgorithm.EXTRUSION,
            MeshAlgorithm.REVOLUTION,
            MeshAlgorithm.DELAUNAY_3D,
            MeshAlgorithm.ALPHA_SHAPE,
        ]
        
        for algorithm in algorithms:
            config = MeshConfig(algorithm=algorithm)
            generator = ShadowMeshGenerator(config)
            mesh = generator.generate(circular_contour)
            
            assert mesh.n_vertices > 0, f"Algorithm {algorithm.value} failed"
            assert mesh.n_faces > 0, f"Algorithm {algorithm.value} produced no faces"
    
    def test_custom_depth(self, circular_contour):
        """Test custom extrusion depth."""
        generator = ShadowMeshGenerator()
        depth = 0.1
        
        mesh = generator.generate(circular_contour, depth=depth)
        
        # Check that Z bounds match depth
        min_b, max_b = mesh.bounds
        z_range = max_b[2] - min_b[2]
        assert abs(z_range - depth) < 1e-5
    
    def test_empty_contour(self):
        """Test handling of empty contour."""
        generator = ShadowMeshGenerator()
        empty_contour = np.zeros((0, 2), dtype=np.float32)
        
        mesh = generator.generate(empty_contour)
        
        assert mesh.n_vertices == 0
        assert mesh.n_faces == 0
    
    def test_small_contour(self):
        """Test handling of very small contour."""
        generator = ShadowMeshGenerator()
        small_contour = np.array([[0, 0], [0.01, 0]], dtype=np.float32)
        
        mesh = generator.generate(small_contour)
        
        # Should handle gracefully
        assert mesh.n_vertices >= 0
    
    def test_mesh_volume(self, circular_contour):
        """Test that mesh volume is reasonable."""
        generator = ShadowMeshGenerator()
        depth = 0.05
        
        mesh = generator.generate(circular_contour, depth=depth)
        
        # Expected volume: π * r² * depth
        radius = 0.05
        expected_volume = np.pi * radius ** 2 * depth
        
        # Allow 20% error due to discretization
        relative_error = abs(mesh.volume - expected_volume) / expected_volume
        assert relative_error < 0.2, f"Volume error too large: {relative_error}"
    
    def test_generation_timing(self, circular_contour):
        """Test that generation meets timing requirements."""
        generator = ShadowMeshGenerator()
        
        import time
        n_iterations = 100
        
        start = time.perf_counter()
        for _ in range(n_iterations):
            mesh = generator.generate(circular_contour)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        avg_time = elapsed_ms / n_iterations
        
        # Should be under 15ms
        assert avg_time < 15.0, f"Generation too slow: {avg_time:.2f}ms"


class TestMeshQuality:
    """Tests for mesh quality metrics."""
    
    def test_triangle_quality(self):
        """Test that generated triangles have reasonable quality."""
        generator = ShadowMeshGenerator()
        
        theta = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        mesh = generator.generate(contour)
        
        # Check triangle aspect ratios
        for face in mesh.faces:
            v0, v1, v2 = mesh.vertices[face]
            
            # Edge lengths
            e0 = np.linalg.norm(v1 - v0)
            e1 = np.linalg.norm(v2 - v1)
            e2 = np.linalg.norm(v0 - v2)
            
            # Aspect ratio (max edge / min edge)
            edges = [e0, e1, e2]
            aspect = max(edges) / (min(edges) + 1e-10)
            
            # Aspect ratio should be reasonable
            assert aspect < 10.0, f"Triangle has poor aspect ratio: {aspect}"
    
    def test_normal_consistency(self):
        """Test that normals are consistent."""
        generator = ShadowMeshGenerator()
        
        theta = np.linspace(0, 2 * np.pi, 32, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        mesh = generator.generate(contour)
        
        # Check that normals are unit length
        for normal in mesh.normals:
            length = np.linalg.norm(normal)
            if length > 1e-10:
                assert abs(length - 1.0) < 0.1, f"Normal not unit length: {length}"


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_very_large_contour(self):
        """Test handling of very large contour."""
        generator = ShadowMeshGenerator()
        
        # Large number of points
        theta = np.linspace(0, 2 * np.pi, 1000, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        mesh = generator.generate(contour)
        
        assert mesh.n_vertices > 0
    
    def test_self_intersecting_contour(self):
        """Test handling of self-intersecting contour."""
        generator = ShadowMeshGenerator()
        
        # Figure-8 shape (self-intersecting)
        t = np.linspace(0, 2 * np.pi, 100)
        contour = np.column_stack([
            0.05 * np.sin(t),
            0.05 * np.sin(2 * t)
        ]).astype(np.float32)
        
        # Should handle gracefully
        mesh = generator.generate(contour)
        assert mesh.n_vertices >= 0
    
    def test_degenerate_contour(self):
        """Test handling of degenerate (all same point) contour."""
        generator = ShadowMeshGenerator()
        
        # All points at same location
        contour = np.ones((10, 2), dtype=np.float32) * 0.05
        
        mesh = generator.generate(contour)
        
        # Should handle gracefully
        assert mesh.n_vertices >= 0


class TestPerformance:
    """Performance benchmarks."""
    
    @pytest.mark.parametrize("n_points", [16, 32, 64, 128, 256])
    def test_scaling(self, n_points):
        """Test scaling with number of contour points."""
        generator = ShadowMeshGenerator()
        
        theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        import time
        n_iterations = 100
        
        start = time.perf_counter()
        for _ in range(n_iterations):
            mesh = generator.generate(contour)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        avg_time = elapsed_ms / n_iterations
        
        print(f"\n  n_points={n_points}: {avg_time:.3f}ms")
        
        # Should scale roughly linearly
        assert avg_time < 15.0
    
    def test_memory_usage(self):
        """Test memory usage is reasonable."""
        import tracemalloc
        
        generator = ShadowMeshGenerator()
        
        theta = np.linspace(0, 2 * np.pi, 256, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        tracemalloc.start()
        
        # Generate multiple meshes
        meshes = []
        for _ in range(10):
            mesh = generator.generate(contour)
            meshes.append(mesh)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory per mesh should be under 50MB / 10 = 5MB
        memory_per_mesh = current / 10
        assert memory_per_mesh < 5 * 1024 * 1024, f"Memory usage too high: {memory_per_mesh / 1024 / 1024:.1f}MB"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
