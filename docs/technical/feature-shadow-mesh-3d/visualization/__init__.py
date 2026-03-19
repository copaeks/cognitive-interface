"""
Visualization modules for Shadow Mesh 3D.

Provides 3D mesh visualization using matplotlib and optional Open3D.
"""

from .mesh_viewer import MeshViewer, VisualizationConfig, create_comparison_figure

__all__ = [
    "MeshViewer",
    "VisualizationConfig",
    "create_comparison_figure",
]
