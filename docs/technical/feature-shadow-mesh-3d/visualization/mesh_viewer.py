"""
3D Mesh Visualization
=====================

Interactive 3D mesh visualization using matplotlib (fallback) and
optional Open3D/trimesh for advanced rendering.

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
import warnings

from mesh_generator import Mesh3D
from physics_inference import PhysicsProperties


@dataclass
class VisualizationConfig:
    """Configuration for mesh visualization."""
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 100
    background_color: str = 'white'
    mesh_color: Optional[str] = None
    show_edges: bool = True
    edge_color: str = 'black'
    edge_width: float = 0.5
    show_vertices: bool = False
    vertex_size: float = 10
    show_normals: bool = False
    normal_length: float = 0.01
    camera_distance: float = 0.3
    elevation: float = 30
    azimuth: float = -60


class MeshViewer:
    """
    3D mesh visualization tool.
    
    Provides both simple matplotlib-based visualization and
    optional advanced rendering with Open3D.
    
    Example:
        >>> from mesh_generator import ShadowMeshGenerator
        >>> generator = ShadowMeshGenerator()
        >>> mesh = generator.generate(contour)
        >>> viewer = MeshViewer()
        >>> viewer.plot_mesh(mesh)
        >>> viewer.show()
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize mesh viewer.
        
        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()
        self._figure = None
        self._axes = None
        self._has_open3d = False
        self._has_trimesh = False
        
        self._check_optional_deps()
    
    def _check_optional_deps(self) -> None:
        """Check for optional visualization dependencies."""
        try:
            import open3d as o3d
            self._has_open3d = True
        except ImportError:
            pass
        
        try:
            import trimesh
            self._has_trimesh = True
        except ImportError:
            pass
    
    def plot_mesh(
        self,
        mesh: Mesh3D,
        physics_props: Optional[PhysicsProperties] = None,
        title: Optional[str] = None,
        ax=None,
    ) -> Any:
        """
        Plot a single mesh using matplotlib.
        
        Args:
            mesh: Mesh3D object to plot
            physics_props: Optional physics properties for coloring
            title: Optional plot title
            ax: Optional matplotlib axes (creates new if None)
            
        Returns:
            Matplotlib axes object
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        except ImportError:
            raise ImportError("matplotlib is required for visualization")
        
        if ax is None:
            if self._figure is None:
                self._figure = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
            ax = self._figure.add_subplot(111, projection='3d')
        
        self._axes = ax
        
        # Determine mesh color
        if physics_props is not None:
            color = self._physics_to_color(physics_props)
        elif self.config.mesh_color:
            color = self.config.mesh_color
        else:
            color = 'lightblue'
        
        # Create 3D polygon collection
        verts = mesh.vertices[mesh.faces]
        
        # Handle vertex colors
        face_colors = None
        if mesh.vertex_colors is not None:
            # Average vertex colors for each face
            face_colors = []
            for face in mesh.faces:
                face_color = np.mean(mesh.vertex_colors[face], axis=0)
                face_colors.append(face_color)
            face_colors = np.array(face_colors)
        
        poly3d = Poly3DCollection(
            verts,
            facecolors=face_colors if face_colors is not None else color,
            edgecolors=self.config.edge_color if self.config.show_edges else 'none',
            linewidths=self.config.edge_width,
            alpha=0.9,
        )
        
        ax.add_collection3d(poly3d)
        
        # Set axis limits
        min_bounds, max_bounds = mesh.bounds
        margin = 0.1 * np.max(max_bounds - min_bounds)
        ax.set_xlim(min_bounds[0] - margin, max_bounds[0] + margin)
        ax.set_ylim(min_bounds[1] - margin, max_bounds[1] + margin)
        ax.set_zlim(min_bounds[2] - margin, max_bounds[2] + margin)
        
        # Set labels and title
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        
        if title:
            ax.set_title(title)
        elif physics_props:
            ax.set_title(f"{physics_props.material_type.value} (rigidity: {physics_props.rigidity:.2f})")
        
        # Set view angle
        ax.view_init(elev=self.config.elevation, azim=self.config.azimuth)
        
        # Add physics info as text
        if physics_props:
            info_text = (
                f"Mass: {physics_props.mass*1000:.1f}g\n"
                f"Density: {physics_props.density:.0f} kg/m³\n"
                f"Confidence: {physics_props.confidence:.2f}"
            )
            ax.text2D(0.02, 0.98, info_text, transform=ax.transAxes,
                     verticalalignment='top', fontsize=8,
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        return ax
    
    def plot_comparison(
        self,
        meshes: List[Mesh3D],
        titles: Optional[List[str]] = None,
        physics_props_list: Optional[List[PhysicsProperties]] = None,
        n_cols: int = 2,
    ) -> Any:
        """
        Plot multiple meshes for comparison.
        
        Args:
            meshes: List of Mesh3D objects
            titles: Optional list of titles
            physics_props_list: Optional list of physics properties
            n_cols: Number of columns in subplot grid
            
        Returns:
            Matplotlib figure object
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for visualization")
        
        n_meshes = len(meshes)
        n_rows = (n_meshes + n_cols - 1) // n_cols
        
        self._figure = plt.figure(figsize=(self.config.figsize[0] * n_cols // 2,
                                          self.config.figsize[1] * n_rows // 2),
                                 dpi=self.config.dpi)
        
        for i, mesh in enumerate(meshes):
            ax = self._figure.add_subplot(n_rows, n_cols, i + 1, projection='3d')
            title = titles[i] if titles else None
            props = physics_props_list[i] if physics_props_list else None
            self.plot_mesh(mesh, props, title, ax)
        
        plt.tight_layout()
        return self._figure
    
    def plot_contour_2d(
        self,
        contour: NDArray[np.float32],
        confidence: Optional[NDArray[np.float32]] = None,
        title: str = "2D Shadow Contour",
    ) -> Any:
        """
        Plot 2D contour with confidence heatmap.
        
        Args:
            contour: (N, 2) contour points
            confidence: Optional (N,) confidence values
            title: Plot title
            
        Returns:
            Matplotlib axes object
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for visualization")
        
        if self._figure is None:
            self._figure, self._axes = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        
        ax = self._axes
        
        # Plot contour
        if confidence is not None:
            scatter = ax.scatter(contour[:, 0], contour[:, 1],
                               c=confidence, cmap='RdYlGn',
                               s=50, edgecolors='black', linewidths=0.5)
            plt.colorbar(scatter, ax=ax, label='Confidence')
        else:
            ax.plot(contour[:, 0], contour[:, 1], 'b-', linewidth=2)
            ax.scatter(contour[:, 0], contour[:, 1], c='blue', s=50)
        
        # Close the contour line
        closed = np.vstack([contour, contour[0]])
        ax.plot(closed[:, 0], closed[:, 1], 'k--', linewidth=1, alpha=0.5)
        
        ax.set_aspect('equal')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        return ax
    
    def visualize_with_open3d(
        self,
        mesh: Mesh3D,
        physics_props: Optional[PhysicsProperties] = None,
        window_name: str = "Shadow Mesh 3D",
    ) -> None:
        """
        Visualize mesh using Open3D (if available).
        
        Args:
            mesh: Mesh3D object
            physics_props: Optional physics properties
            window_name: Window title
        """
        if not self._has_open3d:
            warnings.warn("Open3D not available, falling back to matplotlib")
            self.plot_mesh(mesh, physics_props)
            self.show()
            return
        
        import open3d as o3d
        
        # Convert to Open3D mesh
        o3d_mesh = o3d.geometry.TriangleMesh()
        o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
        o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)
        o3d_mesh.vertex_normals = o3d.utility.Vector3dVector(mesh.normals)
        
        # Set vertex colors
        if mesh.vertex_colors is not None:
            o3d_mesh.vertex_colors = o3d.utility.Vector3dVector(mesh.vertex_colors)
        elif physics_props is not None:
            color = self._physics_to_color(physics_props, as_array=True)
            colors = np.tile(color, (mesh.n_vertices, 1))
            o3d_mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
        
        # Compute normals if not present
        if not o3d_mesh.has_vertex_normals():
            o3d_mesh.compute_vertex_normals()
        
        # Visualize
        o3d.visualization.draw_geometries([o3d_mesh], window_name=window_name)
    
    def create_rotating_gif(
        self,
        mesh: Mesh3D,
        output_path: str,
        physics_props: Optional[PhysicsProperties] = None,
        n_frames: int = 36,
        fps: int = 10,
    ) -> None:
        """
        Create rotating GIF animation of mesh.
        
        Args:
            mesh: Mesh3D object
            output_path: Output GIF file path
            physics_props: Optional physics properties
            n_frames: Number of frames
            fps: Frames per second
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.animation import FuncAnimation, PillowWriter
        except ImportError:
            raise ImportError("matplotlib is required for GIF creation")
        
        self._figure = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        ax = self._figure.add_subplot(111, projection='3d')
        
        self.plot_mesh(mesh, physics_props, ax=ax)
        
        def rotate(frame):
            ax.view_init(elev=self.config.elevation, azim=frame * 360 / n_frames)
            return ax,
        
        anim = FuncAnimation(self._figure, rotate, frames=n_frames, interval=1000/fps, blit=False)
        
        writer = PillowWriter(fps=fps)
        anim.save(output_path, writer=writer)
        
        plt.close(self._figure)
        self._figure = None
    
    def _physics_to_color(
        self,
        physics_props: PhysicsProperties,
        as_array: bool = False,
    ) -> Union[str, NDArray[np.float32]]:
        """Convert physics properties to color."""
        from physics_inference import MaterialType
        
        colors = {
            MaterialType.RIGID_SOLID: '#B0B8C0',    # Gray-blue
            MaterialType.SOFT_SOLID: '#F2A65A',      # Orange
            MaterialType.LIQUID: '#4D9DE0',          # Blue
            MaterialType.GRANULAR: '#D4B483',        # Tan
            MaterialType.GAS: '#E8F4F8',             # Light blue
            MaterialType.UNKNOWN: '#808080',         # Gray
        }
        
        hex_color = colors.get(physics_props.material_type, '#808080')
        
        if as_array:
            # Convert hex to RGB array
            hex_color = hex_color.lstrip('#')
            rgb = np.array([int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)
            return rgb
        
        return hex_color
    
    def show(self) -> None:
        """Show the current plot."""
        try:
            import matplotlib.pyplot as plt
            plt.tight_layout()
            plt.show()
        except ImportError:
            pass
    
    def save(self, filepath: str, dpi: Optional[int] = None) -> None:
        """
        Save current figure to file.
        
        Args:
            filepath: Output file path
            dpi: Optional DPI override
        """
        if self._figure is None:
            raise RuntimeError("No figure to save")
        
        try:
            import matplotlib.pyplot as plt
            self._figure.savefig(filepath, dpi=dpi or self.config.dpi,
                               bbox_inches='tight', facecolor=self.config.background_color)
        except ImportError:
            raise ImportError("matplotlib is required for saving")
    
    def clear(self) -> None:
        """Clear current figure."""
        if self._figure is not None:
            try:
                import matplotlib.pyplot as plt
                plt.close(self._figure)
            except ImportError:
                pass
        self._figure = None
        self._axes = None


def create_comparison_figure(
    contour_2d: NDArray[np.float32],
    mesh_3d: Mesh3D,
    physics_props: Optional[PhysicsProperties] = None,
    output_path: Optional[str] = None,
) -> Any:
    """
    Create a comparison figure showing 2D contour and 3D mesh.
    
    Args:
        contour_2d: 2D contour points
        mesh_3d: 3D mesh
        physics_props: Optional physics properties
        output_path: Optional output file path
        
    Returns:
        Matplotlib figure object
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required")
    
    fig = plt.figure(figsize=(14, 6), dpi=100)
    
    # 2D contour
    ax1 = fig.add_subplot(121)
    ax1.plot(contour_2d[:, 0], contour_2d[:, 1], 'b-', linewidth=2)
    ax1.scatter(contour_2d[:, 0], contour_2d[:, 1], c='blue', s=50)
    closed = np.vstack([contour_2d, contour_2d[0]])
    ax1.plot(closed[:, 0], closed[:, 1], 'k--', linewidth=1, alpha=0.5)
    ax1.set_aspect('equal')
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_title('2D Shadow Contour')
    ax1.grid(True, alpha=0.3)
    
    # 3D mesh
    viewer = MeshViewer()
    ax2 = fig.add_subplot(122, projection='3d')
    viewer.plot_mesh(mesh_3d, physics_props, ax=ax2)
    ax2.set_title('3D Reconstructed Mesh')
    
    plt.tight_layout()
    
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
    
    return fig


def benchmark_visualization():
    """Benchmark visualization performance."""
    import time
    from mesh_generator import ShadowMeshGenerator
    from physics_inference import PhysicsProperties, MaterialType, ShadowFeatures, PhysicsInferenceEngine
    
    print("=" * 60)
    print("VISUALIZATION BENCHMARK")
    print("=" * 60)
    
    # Generate test mesh
    generator = ShadowMeshGenerator()
    theta = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    contour = np.column_stack([
        0.05 * np.cos(theta),
        0.05 * np.sin(theta)
    ]).astype(np.float32)
    
    mesh = generator.generate(contour)
    
    # Infer physics
    features = ShadowFeatures.from_contour(contour)
    engine = PhysicsInferenceEngine()
    physics = engine.infer_properties(features, mesh.volume)
    
    viewer = MeshViewer()
    
    # Benchmark matplotlib plotting
    n_iterations = 100
    start = time.perf_counter()
    
    for _ in range(n_iterations):
        viewer.plot_mesh(mesh, physics)
        viewer.clear()
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"\nMesh: {mesh.n_vertices} vertices, {mesh.n_faces} faces")
    print(f"Matplotlib plot time: {elapsed_ms/n_iterations:.3f}ms")
    
    # Check Open3D availability
    if viewer._has_open3d:
        print("Open3D: Available")
    else:
        print("Open3D: Not available")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    benchmark_visualization()
