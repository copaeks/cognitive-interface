"""
glTF 2.0 Format Exporter
========================

Exports 3D meshes to glTF 2.0 format (GL Transmission Format).
Supports both .gltf (JSON + external buffers) and .glb (binary) formats.
Compatible with Blender, Unreal Engine, Unity, Three.js, and more.

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Optional, Dict, List, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import base64
import struct
import time

from mesh_generator import Mesh3D
from physics_inference import PhysicsProperties


@dataclass
class glTFExportConfig:
    """Configuration for glTF export."""
    format: str = "glb"  # "gltf" or "glb"
    embed_buffers: bool = True  # Embed buffers as base64 in JSON
    include_normals: bool = True
    include_uvs: bool = True
    include_colors: bool = True
    flip_yz: bool = False  # Convert from Y-up to Z-up if needed
    scale: float = 1.0
    compress: bool = False  # Use Draco compression (not implemented)


class glTFExporter:
    """
    Export 3D meshes to glTF 2.0 format.
    
    glTF (GL Transmission Format) is a modern, efficient 3D format
    designed for web and real-time applications.
    
    Supports:
    - .gltf format (JSON with external or embedded buffers)
    - .glb format (binary container)
    - PBR materials based on physics properties
    - Full vertex attributes (position, normal, UV, color)
    
    Example:
        >>> from mesh_generator import ShadowMeshGenerator
        >>> generator = ShadowMeshGenerator()
        >>> mesh = generator.generate(contour)
        >>> exporter = glTFExporter()
        >>> exporter.export(mesh, "output.glb", physics_props)
    """
    
    def __init__(self, config: Optional[glTFExportConfig] = None):
        """
        Initialize glTF exporter.
        
        Args:
            config: Export configuration
        """
        self.config = config or glTFExportConfig()
    
    def export(
        self,
        mesh: Mesh3D,
        filepath: Union[str, Path],
        physics_props: Optional[PhysicsProperties] = None,
    ) -> Dict[str, Any]:
        """
        Export mesh to glTF file.
        
        Args:
            mesh: Mesh3D object to export
            filepath: Output file path (.gltf or .glb)
            physics_props: Optional physics properties for PBR material
            
        Returns:
            Dictionary with export metadata
        """
        start_time = time.perf_counter()
        filepath = Path(filepath)
        
        # Determine format from extension
        if filepath.suffix.lower() == '.glb':
            self.config.format = 'glb'
        elif filepath.suffix.lower() == '.gltf':
            self.config.format = 'gltf'
        else:
            filepath = filepath.with_suffix('.glb')
            self.config.format = 'glb'
        
        # Build glTF structure
        gltf_data = self._build_gltf(mesh, physics_props)
        
        # Write file
        if self.config.format == 'glb':
            self._write_glb(gltf_data, filepath)
        else:
            self._write_gltf(gltf_data, filepath)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        return {
            'filepath': str(filepath),
            'format': self.config.format,
            'vertices_exported': mesh.n_vertices,
            'faces_exported': mesh.n_faces,
            'export_time_ms': elapsed_ms,
        }
    
    def _build_gltf(
        self,
        mesh: Mesh3D,
        physics_props: Optional[PhysicsProperties],
    ) -> Dict[str, Any]:
        """Build glTF JSON structure."""
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "ShadowMesh 3D",
                "copyright": "2024 ShadowMesh Project",
            },
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [],
            "accessors": [],
            "bufferViews": [],
            "buffers": [],
        }
        
        # Add material if physics properties provided
        if physics_props:
            gltf["materials"] = [self._create_material(physics_props)]
        
        # Build mesh primitive
        primitive = self._build_primitive(mesh, physics_props is not None)
        gltf["meshes"].append({"primitives": [primitive]})
        
        # Build buffer and accessors
        buffer_data, accessors, buffer_views = self._build_buffer(mesh)
        gltf["accessors"] = accessors
        gltf["bufferViews"] = buffer_views
        
        # Embed or reference buffer
        if self.config.embed_buffers:
            gltf["buffers"].append({
                "uri": f"data:application/octet-stream;base64,{base64.b64encode(buffer_data).decode()}",
                "byteLength": len(buffer_data),
            })
        else:
            # External buffer file
            gltf["buffers"].append({
                "uri": "buffer.bin",
                "byteLength": len(buffer_data),
            })
        
        return {
            "json": gltf,
            "buffer": buffer_data,
        }
    
    def _build_primitive(
        self,
        mesh: Mesh3D,
        has_material: bool,
    ) -> Dict[str, Any]:
        """Build mesh primitive."""
        primitive = {
            "mode": 4,  # TRIANGLES
            "attributes": {},
        }
        
        accessor_idx = 0
        
        # Position (required)
        primitive["attributes"]["POSITION"] = accessor_idx
        accessor_idx += 1
        
        # Normal
        if self.config.include_normals and len(mesh.normals) > 0:
            primitive["attributes"]["NORMAL"] = accessor_idx
            accessor_idx += 1
        
        # UV
        if self.config.include_uvs and len(mesh.uvs) > 0:
            primitive["attributes"]["TEXCOORD_0"] = accessor_idx
            accessor_idx += 1
        
        # Color
        if self.config.include_colors and mesh.vertex_colors is not None:
            primitive["attributes"]["COLOR_0"] = accessor_idx
            accessor_idx += 1
        
        # Indices
        primitive["indices"] = accessor_idx
        
        # Material
        if has_material:
            primitive["material"] = 0
        
        return primitive
    
    def _build_buffer(
        self,
        mesh: Mesh3D,
    ) -> Tuple[bytes, List[Dict], List[Dict]]:
        """Build binary buffer with all vertex data."""
        accessors = []
        buffer_views = []
        buffer_data = bytearray()
        
        byte_offset = 0
        view_idx = 0
        
        # Vertices (required)
        vertices = mesh.vertices.copy()
        if self.config.flip_yz:
            vertices[:, [1, 2]] = vertices[:, [2, 1]]
        vertices = vertices * self.config.scale
        
        vertex_bytes = vertices.astype(np.float32).tobytes()
        buffer_data.extend(vertex_bytes)
        
        min_vals = vertices.min(axis=0).tolist()
        max_vals = vertices.max(axis=0).tolist()
        
        accessors.append({
            "bufferView": view_idx,
            "componentType": 5126,  # FLOAT
            "count": mesh.n_vertices,
            "type": "VEC3",
            "min": min_vals,
            "max": max_vals,
        })
        
        buffer_views.append({
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": len(vertex_bytes),
            "target": 34962,  # ARRAY_BUFFER
        })
        
        byte_offset += len(vertex_bytes)
        view_idx += 1
        
        # Normals
        if self.config.include_normals and len(mesh.normals) > 0:
            normals = mesh.normals.copy()
            if self.config.flip_yz:
                normals[:, [1, 2]] = normals[:, [2, 1]]
            
            normal_bytes = normals.astype(np.float32).tobytes()
            buffer_data.extend(normal_bytes)
            
            accessors.append({
                "bufferView": view_idx,
                "componentType": 5126,  # FLOAT
                "count": mesh.n_vertices,
                "type": "VEC3",
            })
            
            buffer_views.append({
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(normal_bytes),
                "target": 34962,  # ARRAY_BUFFER
            })
            
            byte_offset += len(normal_bytes)
            view_idx += 1
        
        # UVs
        if self.config.include_uvs and len(mesh.uvs) > 0:
            uv_bytes = mesh.uvs.astype(np.float32).tobytes()
            buffer_data.extend(uv_bytes)
            
            accessors.append({
                "bufferView": view_idx,
                "componentType": 5126,  # FLOAT
                "count": mesh.n_vertices,
                "type": "VEC2",
            })
            
            buffer_views.append({
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(uv_bytes),
                "target": 34962,  # ARRAY_BUFFER
            })
            
            byte_offset += len(uv_bytes)
            view_idx += 1
        
        # Colors
        if self.config.include_colors and mesh.vertex_colors is not None:
            color_bytes = mesh.vertex_colors.astype(np.float32).tobytes()
            buffer_data.extend(color_bytes)
            
            accessors.append({
                "bufferView": view_idx,
                "componentType": 5126,  # FLOAT
                "count": mesh.n_vertices,
                "type": "VEC3",
            })
            
            buffer_views.append({
                "buffer": 0,
                "byteOffset": byte_offset,
                "byteLength": len(color_bytes),
                "target": 34962,  # ARRAY_BUFFER
            })
            
            byte_offset += len(color_bytes)
            view_idx += 1
        
        # Indices (must be aligned to 4 bytes)
        if byte_offset % 4 != 0:
            padding = 4 - (byte_offset % 4)
            buffer_data.extend(b'\x00' * padding)
            byte_offset += padding
        
        indices = mesh.faces.astype(np.uint16).flatten()
        index_bytes = indices.tobytes()
        buffer_data.extend(index_bytes)
        
        accessors.append({
            "bufferView": view_idx,
            "componentType": 5123,  # UNSIGNED_SHORT
            "count": len(indices),
            "type": "SCALAR",
        })
        
        buffer_views.append({
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": len(index_bytes),
            "target": 34963,  # ELEMENT_ARRAY_BUFFER
        })
        
        return bytes(buffer_data), accessors, buffer_views
    
    def _create_material(self, physics_props: PhysicsProperties) -> Dict[str, Any]:
        """Create PBR material from physics properties."""
        # Base color based on material type
        base_color = self._material_type_to_rgba(physics_props.material_type)
        
        # Metallic based on rigidity
        metallic = physics_props.rigidity * 0.8
        
        # Roughness inversely related to rigidity
        roughness = 1.0 - physics_props.rigidity * 0.7
        
        material = {
            "name": f"shadow_{physics_props.material_type.value}",
            "pbrMetallicRoughness": {
                "baseColorFactor": base_color,
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
            "doubleSided": True,
        }
        
        # Add physics properties as extras
        material["extras"] = {
            "physics": {
                "material_type": physics_props.material_type.value,
                "rigidity": physics_props.rigidity,
                "density_kg_m3": physics_props.density,
                "mass_kg": physics_props.mass,
                "youngs_modulus_pa": physics_props.youngs_modulus,
                "friction_coefficient": physics_props.friction_coefficient,
                "restitution": physics_props.restitution,
                "confidence": physics_props.confidence,
            }
        }
        
        return material
    
    def _material_type_to_rgba(self, material_type: Any) -> List[float]:
        """Convert material type to RGBA color."""
        from physics_inference import MaterialType
        
        colors = {
            MaterialType.RIGID_SOLID: [0.7, 0.72, 0.75, 1.0],    # Silver/gray
            MaterialType.SOFT_SOLID: [0.95, 0.6, 0.4, 1.0],      # Orange
            MaterialType.LIQUID: [0.3, 0.5, 0.95, 0.8],          # Blue (transparent)
            MaterialType.GRANULAR: [0.85, 0.75, 0.55, 1.0],      # Sand
            MaterialType.GAS: [0.9, 0.95, 1.0, 0.3],             # Light blue (transparent)
            MaterialType.UNKNOWN: [0.5, 0.5, 0.5, 1.0],          # Gray
        }
        
        return colors.get(material_type, [0.5, 0.5, 0.5, 1.0])
    
    def _write_glb(
        self,
        gltf_data: Dict[str, Any],
        filepath: Path,
    ) -> None:
        """Write binary glTF (.glb) file."""
        json_data = json.dumps(gltf_data["json"], separators=(',', ':')).encode()
        buffer_data = gltf_data["buffer"]
        
        # Pad JSON to 4-byte boundary
        json_padding = (4 - (len(json_data) % 4)) % 4
        json_data += b' ' * json_padding
        
        # Pad buffer to 4-byte boundary
        buffer_padding = (4 - (len(buffer_data) % 4)) % 4
        buffer_data += b'\x00' * buffer_padding
        
        # Build GLB header
        header = struct.pack('<4sII',
            b'glTF',  # Magic
            2,        # Version
            12 + 8 + len(json_data) + 8 + len(buffer_data)  # Total length
        )
        
        # JSON chunk
        json_chunk = struct.pack('<I4s', len(json_data), b'JSON') + json_data
        
        # BIN chunk
        bin_chunk = struct.pack('<I4s', len(buffer_data), b'BIN\x00') + buffer_data
        
        # Write file
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(json_chunk)
            f.write(bin_chunk)
    
    def _write_gltf(
        self,
        gltf_data: Dict[str, Any],
        filepath: Path,
    ) -> None:
        """Write JSON glTF (.gltf) file."""
        gltf_json = gltf_data["json"]
        buffer_data = gltf_data["buffer"]
        
        if not self.config.embed_buffers:
            # Write external buffer file
            bin_path = filepath.with_suffix('.bin')
            with open(bin_path, 'wb') as f:
                f.write(buffer_data)
        
        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(gltf_json, f, indent=2)
    
    def export_batch(
        self,
        meshes: List[Mesh3D],
        filepaths: List[Union[str, Path]],
        physics_props_list: Optional[List[PhysicsProperties]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export multiple meshes to glTF files.
        
        Args:
            meshes: List of Mesh3D objects
            filepaths: List of output file paths
            physics_props_list: Optional list of physics properties
            
        Returns:
            List of export metadata dictionaries
        """
        results = []
        
        for i, (mesh, filepath) in enumerate(zip(meshes, filepaths)):
            props = physics_props_list[i] if physics_props_list else None
            result = self.export(mesh, filepath, props)
            results.append(result)
        
        return results


def validate_gltf(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Basic validation of glTF file.
    
    Args:
        filepath: Path to glTF file
        
    Returns:
        Validation results dictionary
    """
    filepath = Path(filepath)
    results = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'info': {},
    }
    
    try:
        if filepath.suffix.lower() == '.glb':
            with open(filepath, 'rb') as f:
                magic = f.read(4)
                if magic != b'glTF':
                    results['errors'].append("Invalid GLB magic bytes")
                    return results
                
                version = struct.unpack('<I', f.read(4))[0]
                length = struct.unpack('<I', f.read(4))[0]
                
                results['info']['version'] = version
                results['info']['length'] = length
        else:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                if 'asset' not in data:
                    results['errors'].append("Missing asset section")
                elif 'version' not in data.get('asset', {}):
                    results['errors'].append("Missing glTF version")
                else:
                    results['info']['version'] = data['asset']['version']
                
                if 'meshes' not in data or not data['meshes']:
                    results['warnings'].append("No meshes in file")
                else:
                    results['info']['mesh_count'] = len(data['meshes'])
        
        if not results['errors']:
            results['valid'] = True
            
    except Exception as e:
        results['errors'].append(str(e))
    
    return results


def benchmark_gltf_export():
    """Benchmark glTF export performance."""
    import time
    from mesh_generator import ShadowMeshGenerator
    from physics_inference import PhysicsProperties, MaterialType
    
    print("=" * 60)
    print("glTF EXPORT BENCHMARK")
    print("=" * 60)
    
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
    
    exporter = glTFExporter()
    
    # Warm-up
    for _ in range(10):
        exporter.export(mesh, "/tmp/test.glb", physics)
    
    # Benchmark GLB
    n_iterations = 100
    start = time.perf_counter()
    
    for _ in range(n_iterations):
        exporter.export(mesh, "/tmp/test.glb", physics)
    
    glb_time = (time.perf_counter() - start) * 1000
    
    # Benchmark glTF
    exporter.config.format = 'gltf'
    start = time.perf_counter()
    
    for _ in range(n_iterations):
        exporter.export(mesh, "/tmp/test.gltf", physics)
    
    gltf_time = (time.perf_counter() - start) * 1000
    
    print(f"\nMesh: {mesh.n_vertices} vertices, {mesh.n_faces} faces")
    print(f"GLB export time: {glb_time/n_iterations:.3f}ms")
    print(f"glTF export time: {gltf_time/n_iterations:.3f}ms")
    print(f"GLB throughput: {n_iterations/glb_time*1000:.0f} exports/sec")
    
    # Validate exported file
    validation = validate_gltf("/tmp/test.glb")
    print(f"\nValidation: {'PASS' if validation['valid'] else 'FAIL'}")
    if validation['info']:
        print(f"  Info: {validation['info']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    benchmark_gltf_export()
