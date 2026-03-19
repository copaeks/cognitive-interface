"""
Shadow Mesh 3D - 3D Reconstruction with Differentiable Physics
==============================================================

Elevate 2D acoustic shadow contours to full 3D meshes with inferred
physical properties using lightweight neural networks.

Example:
    >>> from shadow_mesh_3d import ShadowMeshGenerator, PhysicsInferenceEngine
    >>> import numpy as np
    >>> 
    >>> # Create 2D contour
    >>> theta = np.linspace(0, 2*np.pi, 64, endpoint=False)
    >>> contour = np.column_stack([0.05*np.cos(theta), 0.05*np.sin(theta)])
    >>> 
    >>> # Generate 3D mesh
    >>> generator = ShadowMeshGenerator()
    >>> mesh = generator.generate(contour)
    >>> 
    >>> # Infer physics
    >>> engine = PhysicsInferenceEngine()
    >>> features = ShadowFeatures.from_contour(contour)
    >>> physics = engine.infer_properties(features, mesh.volume)
"""

__version__ = "1.0.0"
__author__ = "Iván Vankov Fortanet"
__email__ = "fortanet2002@gmail.com"

# Core modules
from mesh_generator import (
    Mesh3D,
    MeshConfig,
    MeshAlgorithm,
    ShadowMeshGenerator,
)

from physics_inference import (
    MaterialType,
    PhysicsProperties,
    PhysicsInferenceEngine,
    ShadowFeatures,
    MiniMLP,
)

from material_properties import (
    MaterialProperties,
    MaterialCategory,
    MaterialDatabase,
    get_material_database,
)

# Exporters
from exporters.obj_exporter import OBJExporter, import_obj
from exporters.gltf_exporter import glTFExporter, validate_gltf

# Visualization
from visualization.mesh_viewer import MeshViewer, VisualizationConfig

__all__ = [
    # Version
    "__version__",
    
    # Mesh generation
    "Mesh3D",
    "MeshConfig",
    "MeshAlgorithm",
    "ShadowMeshGenerator",
    
    # Physics inference
    "MaterialType",
    "PhysicsProperties",
    "PhysicsInferenceEngine",
    "ShadowFeatures",
    "MiniMLP",
    
    # Material database
    "MaterialProperties",
    "MaterialCategory",
    "MaterialDatabase",
    "get_material_database",
    
    # Exporters
    "OBJExporter",
    "import_obj",
    "glTFExporter",
    "validate_gltf",
    
    # Visualization
    "MeshViewer",
    "VisualizationConfig",
]
