"""
3D Reconstruction Performance Benchmarks
========================================

Comprehensive benchmarks for 3D mesh reconstruction and physics inference.
Validates performance targets:
- 3D reconstruction: <15ms
- Error: <0.5mm
- Memory: <50MB per object

Run with: python benchmark_3d.py
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import List, Dict, Any, Tuple
import time
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mesh_generator import Mesh3D, MeshConfig, ShadowMeshGenerator
from physics_inference import (
    PhysicsInferenceEngine, ShadowFeatures, PhysicsProperties, MaterialType
)
from material_properties import get_material_database, MaterialCategory
from exporters.obj_exporter import OBJExporter
from exporters.gltf_exporter import glTFExporter


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, name: str):
        self.name = name
        self.measurements: List[float] = []
        self.metadata: Dict[str, Any] = {}
    
    def add(self, value: float):
        """Add a measurement."""
        self.measurements.append(value)
    
    @property
    def mean(self) -> float:
        """Mean value."""
        return np.mean(self.measurements) if self.measurements else 0.0
    
    @property
    def std(self) -> float:
        """Standard deviation."""
        return np.std(self.measurements) if self.measurements else 0.0
    
    @property
    def min(self) -> float:
        """Minimum value."""
        return np.min(self.measurements) if self.measurements else 0.0
    
    @property
    def max(self) -> float:
        """Maximum value."""
        return np.max(self.measurements) if self.measurements else 0.0
    
    @property
    def p95(self) -> float:
        """95th percentile."""
        return np.percentile(self.measurements, 95) if self.measurements else 0.0
    
    @property
    def p99(self) -> float:
        """99th percentile."""
        return np.percentile(self.measurements, 99) if self.measurements else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'mean': self.mean,
            'std': self.std,
            'min': self.min,
            'max': self.max,
            'p95': self.p95,
            'p99': self.p99,
            'n_samples': len(self.measurements),
            'metadata': self.metadata,
        }
    
    def __str__(self) -> str:
        return (f"{self.name}: {self.mean:.3f}±{self.std:.3f}ms "
                f"[min={self.min:.3f}, max={self.max:.3f}, p95={self.p95:.3f}]")


def benchmark_mesh_generation() -> Dict[str, BenchmarkResult]:
    """Benchmark 3D mesh generation."""
    print("\n" + "=" * 60)
    print("MESH GENERATION BENCHMARK")
    print("=" * 60)
    
    results = {}
    
    # Test different contour sizes
    contour_sizes = [16, 32, 64, 128, 256]
    
    for n_points in contour_sizes:
        result = BenchmarkResult(f"mesh_gen_{n_points}pts")
        
        # Create circular contour
        theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        generator = ShadowMeshGenerator()
        
        # Warm-up
        for _ in range(10):
            generator.generate(contour)
        
        # Benchmark
        n_iterations = 1000
        for _ in range(n_iterations):
            start = time.perf_counter()
            mesh = generator.generate(contour)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.add(elapsed_ms)
        
        result.metadata = {
            'n_points': n_points,
            'n_vertices': mesh.n_vertices,
            'n_faces': mesh.n_faces,
        }
        
        results[f"mesh_gen_{n_points}pts"] = result
        print(f"  {result}")
    
    return results


def benchmark_physics_inference() -> Dict[str, BenchmarkResult]:
    """Benchmark physics inference."""
    print("\n" + "=" * 60)
    print("PHYSICS INFERENCE BENCHMARK")
    print("=" * 60)
    
    results = {}
    
    # Test different object types
    test_cases = [
        ("rigid_sphere", _create_rigid_features()),
        ("soft_object", _create_soft_features()),
        ("liquid_drop", _create_liquid_features()),
        ("granular_pile", _create_granular_features()),
    ]
    
    engine = PhysicsInferenceEngine()
    
    for name, features in test_cases:
        result = BenchmarkResult(f"physics_{name}")
        
        volume = 0.001  # 1 liter
        
        # Warm-up
        for _ in range(100):
            engine.infer_properties(features, volume)
        
        # Benchmark
        n_iterations = 10000
        for _ in range(n_iterations):
            start = time.perf_counter()
            props = engine.infer_properties(features, volume)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.add(elapsed_ms)
        
        result.metadata = {
            'material_type': props.material_type.value,
            'rigidity': props.rigidity,
            'density': props.density,
        }
        
        results[f"physics_{name}"] = result
        print(f"  {result}")
    
    return results


def benchmark_export() -> Dict[str, BenchmarkResult]:
    """Benchmark export formats."""
    print("\n" + "=" * 60)
    print("EXPORT BENCHMARK")
    print("=" * 60)
    
    results = {}
    
    # Generate test mesh
    generator = ShadowMeshGenerator()
    theta = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    contour = np.column_stack([
        0.05 * np.cos(theta),
        0.05 * np.sin(theta)
    ]).astype(np.float32)
    mesh = generator.generate(contour)
    
    # Create physics properties
    physics = PhysicsProperties(
        material_type=MaterialType.RIGID_SOLID,
        rigidity=0.9,
        youngs_modulus=70e9,
        density=2700.0,
        mass=0.1,
        volume=0.0001,
        friction_coefficient=0.3,
        restitution=0.5,
        confidence=0.85,
    )
    
    # Benchmark OBJ export
    obj_result = BenchmarkResult("export_obj")
    obj_exporter = OBJExporter()
    
    for _ in range(10):
        obj_exporter.export(mesh, "/tmp/bench_test.obj", physics)
    
    n_iterations = 100
    for _ in range(n_iterations):
        start = time.perf_counter()
        obj_exporter.export(mesh, "/tmp/bench_test.obj", physics)
        elapsed_ms = (time.perf_counter() - start) * 1000
        obj_result.add(elapsed_ms)
    
    results["export_obj"] = obj_result
    print(f"  {obj_result}")
    
    # Benchmark glTF export
    gltf_result = BenchmarkResult("export_gltf")
    gltf_exporter = glTFExporter()
    
    for _ in range(10):
        gltf_exporter.export(mesh, "/tmp/bench_test.glb", physics)
    
    for _ in range(n_iterations):
        start = time.perf_counter()
        gltf_exporter.export(mesh, "/tmp/bench_test.glb", physics)
        elapsed_ms = (time.perf_counter() - start) * 1000
        gltf_result.add(elapsed_ms)
    
    results["export_gltf"] = gltf_result
    print(f"  {gltf_result}")
    
    return results


def benchmark_accuracy() -> Dict[str, Any]:
    """Benchmark reconstruction accuracy."""
    print("\n" + "=" * 60)
    print("ACCURACY BENCHMARK")
    print("=" * 60)
    
    results = {}
    
    # Test with known geometry: circle
    generator = ShadowMeshGenerator()
    
    # Create perfect circle
    theta = np.linspace(0, 2 * np.pi, 256, endpoint=False)
    true_radius = 0.05
    contour = np.column_stack([
        true_radius * np.cos(theta),
        true_radius * np.sin(theta)
    ]).astype(np.float32)
    
    mesh = generator.generate(contour)
    
    # Volume accuracy
    true_area = np.pi * true_radius ** 2
    true_volume = true_area * 0.05  # depth = 0.05
    
    mesh_volume = mesh.volume
    volume_error = abs(mesh_volume - true_volume)
    volume_error_relative = volume_error / true_volume * 100
    
    results['volume_error_m3'] = volume_error
    results['volume_error_relative_pct'] = volume_error_relative
    
    print(f"  Volume error: {volume_error:.8f} m³ ({volume_error_relative:.2f}%)")
    
    # Surface area accuracy
    true_surface = 2 * true_area + 2 * np.pi * true_radius * 0.05
    mesh_surface = mesh.surface_area
    surface_error = abs(mesh_surface - true_surface)
    surface_error_relative = surface_error / true_surface * 100
    
    results['surface_error_m2'] = surface_error
    results['surface_error_relative_pct'] = surface_error_relative
    
    print(f"  Surface error: {surface_error:.8f} m² ({surface_error_relative:.2f}%)")
    
    # Vertex position accuracy
    # Check that contour vertices are close to expected cylinder surface
    # Exclude centroid vertices (last 2 vertices in extrusion mesh)
    max_vertex_error = 0.0
    n_contour = len(theta)
    
    # Only check the original contour vertices (first 2*n_contour vertices)
    # These are the vertices on the top and bottom caps
    for i in range(2 * n_contour):
        vertex = mesh.vertices[i]
        # Distance from expected cylinder surface
        r = np.sqrt(vertex[0]**2 + vertex[1]**2)
        z_error = abs(abs(vertex[2]) - 0.025)
        r_error = abs(r - true_radius)
        error = max(r_error, z_error)
        max_vertex_error = max(max_vertex_error, error)
    
    results['max_vertex_error_m'] = max_vertex_error
    results['max_vertex_error_mm'] = max_vertex_error * 1000
    
    print(f"  Max vertex error: {max_vertex_error*1000:.3f} mm")
    
    # Watertight check
    results['watertight'] = mesh.is_watertight()
    print(f"  Watertight: {mesh.is_watertight()}")
    
    return results


def benchmark_end_to_end() -> Dict[str, BenchmarkResult]:
    """Benchmark end-to-end pipeline."""
    print("\n" + "=" * 60)
    print("END-TO-END PIPELINE BENCHMARK")
    print("=" * 60)
    
    result = BenchmarkResult("end_to_end")
    
    # Setup
    generator = ShadowMeshGenerator()
    engine = PhysicsInferenceEngine()
    obj_exporter = OBJExporter()
    
    # Create test contour
    theta = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    contour = np.column_stack([
        0.05 * np.cos(theta),
        0.05 * np.sin(theta)
    ]).astype(np.float32)
    confidence = np.ones(64, dtype=np.float32) * 0.9
    
    # Warm-up
    for _ in range(10):
        mesh = generator.generate(contour, confidence)
        features = ShadowFeatures.from_contour(contour, confidence)
        physics = engine.infer_properties(features, mesh.volume)
        obj_exporter.export(mesh, "/tmp/e2e_test.obj", physics)
    
    # Benchmark full pipeline
    n_iterations = 100
    for _ in range(n_iterations):
        start = time.perf_counter()
        
        # 1. Generate mesh
        mesh = generator.generate(contour, confidence)
        
        # 2. Extract features
        features = ShadowFeatures.from_contour(contour, confidence)
        
        # 3. Infer physics
        physics = engine.infer_properties(features, mesh.volume)
        
        # 4. Export
        obj_exporter.export(mesh, "/tmp/e2e_test.obj", physics)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        result.add(elapsed_ms)
    
    result.metadata = {
        'n_vertices': mesh.n_vertices,
        'n_faces': mesh.n_faces,
    }
    
    print(f"  {result}")
    
    return {"end_to_end": result}


def benchmark_memory() -> Dict[str, Any]:
    """Benchmark memory usage."""
    print("\n" + "=" * 60)
    print("MEMORY BENCHMARK")
    print("=" * 60)
    
    results = {}
    
    try:
        import tracemalloc
        
        generator = ShadowMeshGenerator()
        
        theta = np.linspace(0, 2 * np.pi, 256, endpoint=False)
        contour = np.column_stack([
            0.05 * np.cos(theta),
            0.05 * np.sin(theta)
        ]).astype(np.float32)
        
        # Measure mesh memory
        tracemalloc.start()
        mesh = generator.generate(contour)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        mesh_memory_mb = current / 1024 / 1024
        results['mesh_memory_mb'] = mesh_memory_mb
        print(f"  Mesh memory: {mesh_memory_mb:.2f} MB")
        
        # Measure multiple meshes
        tracemalloc.start()
        meshes = []
        for _ in range(10):
            meshes.append(generator.generate(contour))
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        total_memory_mb = current / 1024 / 1024
        per_mesh_mb = total_memory_mb / 10
        
        results['total_memory_10_meshes_mb'] = total_memory_mb
        results['per_mesh_memory_mb'] = per_mesh_mb
        
        print(f"  10 meshes memory: {total_memory_mb:.2f} MB")
        print(f"  Per mesh: {per_mesh_mb:.2f} MB")
        
    except ImportError:
        print("  tracemalloc not available, skipping memory benchmark")
        results['error'] = 'tracemalloc not available'
    
    return results


def _create_rigid_features() -> ShadowFeatures:
    """Create features for rigid object."""
    return ShadowFeatures(
        area=0.00785, perimeter=0.314, circularity=1.0,
        aspect_ratio=1.0, convexity=1.0,
        deformation_rate=0.0, motion_stability=1.0,
        shadow_contrast=0.9, edge_sharpness=0.95,
        estimated_thickness=0.1, surface_roughness=0.1,
    )


def _create_soft_features() -> ShadowFeatures:
    """Create features for soft object."""
    return ShadowFeatures(
        area=0.01, perimeter=0.4, circularity=0.7,
        aspect_ratio=1.2, convexity=0.9,
        deformation_rate=0.05, motion_stability=0.7,
        shadow_contrast=0.7, edge_sharpness=0.6,
        estimated_thickness=0.08, surface_roughness=0.4,
    )


def _create_liquid_features() -> ShadowFeatures:
    """Create features for liquid."""
    return ShadowFeatures(
        area=0.005, perimeter=0.25, circularity=0.95,
        aspect_ratio=1.0, convexity=1.0,
        deformation_rate=0.0, motion_stability=0.9,
        shadow_contrast=0.95, edge_sharpness=0.9,
        estimated_thickness=0.02, surface_roughness=0.05,
    )


def _create_granular_features() -> ShadowFeatures:
    """Create features for granular material."""
    return ShadowFeatures(
        area=0.012, perimeter=0.5, circularity=0.5,
        aspect_ratio=1.5, convexity=0.8,
        deformation_rate=0.02, motion_stability=0.5,
        shadow_contrast=0.6, edge_sharpness=0.4,
        estimated_thickness=0.15, surface_roughness=0.8,
    )


def run_all_benchmarks() -> Dict[str, Any]:
    """Run all benchmarks and return results."""
    all_results = {}
    
    print("\n" + "=" * 60)
    print("SHADOW MESH 3D - PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print("\nTargets:")
    print("  - 3D reconstruction: <15ms")
    print("  - Error: <0.5mm")
    print("  - Memory: <50MB per object")
    
    # Run benchmarks
    all_results['mesh_generation'] = benchmark_mesh_generation()
    all_results['physics_inference'] = benchmark_physics_inference()
    all_results['export'] = benchmark_export()
    all_results['accuracy'] = benchmark_accuracy()
    all_results['end_to_end'] = benchmark_end_to_end()
    all_results['memory'] = benchmark_memory()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Check targets
    mesh_results = all_results['mesh_generation']
    fastest_mesh = min(r.mean for r in mesh_results.values())
    slowest_mesh = max(r.mean for r in mesh_results.values())
    
    print(f"\nMesh Generation:")
    print(f"  Fastest: {fastest_mesh:.3f}ms")
    print(f"  Slowest: {slowest_mesh:.3f}ms")
    print(f"  Target: <15ms")
    print(f"  Status: {'PASS' if slowest_mesh < 15.0 else 'FAIL'}")
    
    accuracy = all_results['accuracy']
    max_error_mm = accuracy.get('max_vertex_error_mm', float('inf'))
    
    print(f"\nAccuracy:")
    print(f"  Max vertex error: {max_error_mm:.3f}mm")
    print(f"  Target: <0.5mm")
    print(f"  Status: {'PASS' if max_error_mm < 0.5 else 'FAIL'}")
    
    memory = all_results['memory']
    per_mesh_mb = memory.get('per_mesh_memory_mb', float('inf'))
    
    print(f"\nMemory:")
    print(f"  Per mesh: {per_mesh_mb:.2f}MB")
    print(f"  Target: <50MB")
    print(f"  Status: {'PASS' if per_mesh_mb < 50.0 else 'FAIL'}")
    
    e2e = all_results['end_to_end']['end_to_end']
    print(f"\nEnd-to-End:")
    print(f"  Mean: {e2e.mean:.3f}ms")
    print(f"  P95: {e2e.p95:.3f}ms")
    
    # Overall status
    all_pass = (
        slowest_mesh < 15.0 and
        max_error_mm < 0.5 and
        per_mesh_mb < 50.0
    )
    
    print("\n" + "=" * 60)
    print(f"OVERALL: {'ALL TARGETS MET' if all_pass else 'SOME TARGETS MISSED'}")
    print("=" * 60)
    
    return all_results


def save_results(results: Dict[str, Any], filepath: str):
    """Save benchmark results to JSON."""
    # Convert BenchmarkResult objects to dicts and handle numpy types
    def convert(obj):
        if isinstance(obj, BenchmarkResult):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return obj
    
    converted = convert(results)
    
    with open(filepath, 'w') as f:
        json.dump(converted, f, indent=2)
    
    print(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    results = run_all_benchmarks()
    save_results(results, "/tmp/benchmark_3d_results.json")
