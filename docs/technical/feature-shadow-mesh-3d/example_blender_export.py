"""
Blender Integration Example
===========================

This script demonstrates how to import Shadow Mesh 3D outputs into Blender.
Can be run from Blender's Python console or as a script.

Requirements:
    - Blender 3.6 or newer
    - Shadow Mesh 3D output files (.obj + .json)

Usage:
    1. Open Blender
    2. Go to Scripting tab
    3. Open this file or paste contents
    4. Modify the file paths below
    5. Run script

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

import bpy
import bmesh
import json
import os
from mathutils import Vector


# =============================================================================
# CONFIGURATION - Modify these paths
# =============================================================================

# Path to your exported files
OBJ_FILE_PATH = "/path/to/your/model.obj"  # Change this!
PHYSICS_JSON_PATH = "/path/to/your/physics.json"  # Change this!

# Import options
CREATE_MATERIAL = True
APPLY_PHYSICS_PROPERTIES = True
SET_ORIGIN_TO_CENTER = True
SMOOTH_SHADING = True


# =============================================================================
# BLENDER IMPORT FUNCTIONS
# =============================================================================

def load_physics_properties(json_path: str) -> dict:
    """
    Load physics properties from JSON file.
    
    Args:
        json_path: Path to physics JSON file
        
    Returns:
        Dictionary with physics properties
    """
    if not os.path.exists(json_path):
        print(f"Warning: Physics file not found: {json_path}")
        return {}
    
    with open(json_path, 'r') as f:
        return json.load(f)


def create_pbr_material(name: str, physics: dict) -> bpy.types.Material:
    """
    Create a PBR material based on physics properties.
    
    Args:
        name: Material name
        physics: Physics properties dictionary
        
    Returns:
        Created material
    """
    # Create new material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Get principled BSDF node
    principled = mat.node_tree.nodes["Principled BSDF"]
    
    # Extract properties with defaults
    rigidity = physics.get('rigidity', 0.5)
    material_type = physics.get('material_type', 'unknown')
    
    # Material type colors
    type_colors = {
        'rigid_solid': (0.7, 0.72, 0.75, 1.0),    # Silver
        'soft_solid': (0.95, 0.6, 0.4, 1.0),      # Orange
        'liquid': (0.3, 0.5, 0.95, 0.8),          # Blue (transparent)
        'granular': (0.85, 0.75, 0.55, 1.0),      # Sand
        'gas': (0.9, 0.95, 1.0, 0.3),             # Light blue
        'unknown': (0.5, 0.5, 0.5, 1.0),          # Gray
    }
    
    base_color = type_colors.get(material_type, type_colors['unknown'])
    
    # Set PBR properties
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = rigidity * 0.8
    principled.inputs["Roughness"].default_value = 1.0 - rigidity * 0.7
    principled.inputs["Specular"].default_value = 0.5 + rigidity * 0.5
    
    # Set transparency for liquids/gases
    if material_type in ['liquid', 'gas']:
        principled.inputs["Alpha"].default_value = base_color[3]
        mat.blend_method = 'BLEND'
    
    # Add subsurface for soft materials
    if material_type == 'soft_solid':
        principled.inputs["Subsurface Weight"].default_value = 0.3
        principled.inputs["Subsurface Radius"].default_value = (0.1, 0.05, 0.02)
    
    return mat


def import_obj_with_physics(
    obj_path: str,
    physics_path: str = None,
    create_material: bool = True,
    apply_physics: bool = True,
) -> bpy.types.Object:
    """
    Import OBJ file with physics properties.
    
    Args:
        obj_path: Path to OBJ file
        physics_path: Path to physics JSON file (optional)
        create_material: Whether to create PBR material
        apply_physics: Whether to apply physics properties
        
    Returns:
        Imported object
    """
    # Check if file exists
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"OBJ file not found: {obj_path}")
    
    # Load physics properties
    physics = {}
    if physics_path and apply_physics:
        physics = load_physics_properties(physics_path)
    
    # Import OBJ
    print(f"Importing: {obj_path}")
    bpy.ops.import_scene.obj(
        filepath=obj_path,
        use_smooth_groups=True,
        use_split_objects=False,
        use_split_groups=False,
    )
    
    # Get imported object
    obj = bpy.context.selected_objects[0]
    print(f"Imported object: {obj.name}")
    
    # Apply physics properties as custom properties
    if physics and apply_physics:
        print("Applying physics properties...")
        
        # Core properties
        obj["shadow_material_type"] = physics.get('material_type', 'unknown')
        obj["shadow_rigidity"] = physics.get('rigidity', 0.5)
        obj["shadow_density_kg_m3"] = physics.get('density_kg_m3', 1000.0)
        obj["shadow_mass_kg"] = physics.get('mass_kg', 0.0)
        obj["shadow_volume_m3"] = physics.get('volume_m3', 0.0)
        obj["shadow_youngs_modulus_pa"] = physics.get('youngs_modulus_pa', 1e9)
        obj["shadow_friction"] = physics.get('friction_coefficient', 0.3)
        obj["shadow_restitution"] = physics.get('restitution', 0.5)
        obj["shadow_confidence"] = physics.get('confidence', 0.5)
        
        print(f"  Material: {physics.get('material_type', 'unknown')}")
        print(f"  Rigidity: {physics.get('rigidity', 0.5):.2f}")
        print(f"  Mass: {physics.get('mass_kg', 0.0)*1000:.2f}g")
    
    # Create and apply material
    if create_material and physics:
        mat = create_pbr_material(
            f"{obj.name}_material",
            physics
        )
        
        # Assign material
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        
        print(f"Created material: {mat.name}")
    
    # Set origin to geometry center
    if SET_ORIGIN_TO_CENTER:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # Apply smooth shading
    if SMOOTH_SHADING:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
        
        # Enable auto smooth
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = 0.523599  # 30 degrees
    
    return obj


def setup_physics_simulation(obj: bpy.types.Object, physics: dict):
    """
    Setup rigid body physics simulation for object.
    
    Args:
        obj: Blender object
        physics: Physics properties dictionary
    """
    # Enable rigid body
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    
    # Set mass
    mass = physics.get('mass_kg', 0.1)
    obj.rigid_body.mass = mass
    
    # Set friction
    friction = physics.get('friction_coefficient', 0.5)
    obj.rigid_body.friction = friction
    
    # Set restitution (bounciness)
    restitution = physics.get('restitution', 0.5)
    obj.rigid_body.restitution = restitution
    
    # Set collision shape based on material type
    material_type = physics.get('material_type', 'unknown')
    
    if material_type == 'liquid':
        obj.rigid_body.collision_shape = 'SPHERE'
    elif material_type == 'soft_solid':
        obj.rigid_body.collision_shape = 'CONVEX_HULL'
    else:
        obj.rigid_body.collision_shape = 'MESH'
    
    print(f"Physics simulation setup for {obj.name}")
    print(f"  Mass: {mass:.3f}kg")
    print(f"  Friction: {friction:.2f}")
    print(f"  Restitution: {restitution:.2f}")


def create_ground_plane():
    """Create a ground plane for physics simulation."""
    # Add plane
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, -0.1))
    plane = bpy.context.active_object
    plane.name = "Shadow_Ground"
    
    # Make it a rigid body (passive)
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    
    return plane


def create_camera_and_light():
    """Create default camera and lighting setup."""
    # Add camera
    bpy.ops.object.camera_add(location=(0.3, -0.3, 0.2))
    camera = bpy.context.active_object
    camera.name = "Shadow_Camera"
    camera.rotation_euler = (1.1, 0, 0.785)
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    # Add sun light
    bpy.ops.object.light_add(type='SUN', location=(0.5, 0.5, 1.0))
    sun = bpy.context.active_object
    sun.name = "Shadow_Sun"
    sun.rotation_euler = (0.785, 0, 0.785)
    sun.data.energy = 3.0
    
    return camera, sun


def batch_import(directory: str, pattern: str = "*.obj"):
    """
    Import all OBJ files in a directory.
    
    Args:
        directory: Directory containing OBJ files
        pattern: File pattern to match
    """
    import glob
    
    obj_files = glob.glob(os.path.join(directory, pattern))
    
    print(f"Found {len(obj_files)} OBJ files")
    
    imported_objects = []
    for obj_path in obj_files:
        # Look for corresponding physics file
        base_name = os.path.splitext(obj_path)[0]
        physics_path = base_name + "_physics.json"
        
        if not os.path.exists(physics_path):
            physics_path = None
        
        try:
            obj = import_obj_with_physics(obj_path, physics_path)
            imported_objects.append(obj)
        except Exception as e:
            print(f"Error importing {obj_path}: {e}")
    
    print(f"Successfully imported {len(imported_objects)} objects")
    return imported_objects


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("SHADOW MESH 3D - BLENDER IMPORT")
    print("=" * 60)
    
    # Check if paths are set
    if OBJ_FILE_PATH == "/path/to/your/model.obj":
        print("\nERROR: Please set OBJ_FILE_PATH and PHYSICS_JSON_PATH")
        print("Edit the CONFIGURATION section at the top of this script")
        return
    
    # Clear existing objects (optional)
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.object.delete()
    
    # Import the mesh
    try:
        obj = import_obj_with_physics(
            OBJ_FILE_PATH,
            PHYSICS_JSON_PATH,
            create_material=CREATE_MATERIAL,
            apply_physics=APPLY_PHYSICS_PROPERTIES,
        )
        
        # Load physics for simulation setup
        physics = load_physics_properties(PHYSICS_JSON_PATH)
        
        # Setup physics simulation (optional)
        # setup_physics_simulation(obj, physics)
        
        # Create ground plane (optional)
        # create_ground_plane()
        
        # Create camera and light
        create_camera_and_light()
        
        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print("=" * 60)
        print(f"Object: {obj.name}")
        print(f"Location: {obj.location}")
        print(f"Vertices: {len(obj.data.vertices)}")
        print(f"Faces: {len(obj.data.polygons)}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


# Run main function
if __name__ == "__main__":
    main()


# =============================================================================
# BLENDER PANEL (Optional - adds UI panel)
# =============================================================================

class SHADOW_PT_import_panel(bpy.types.Panel):
    """Shadow Mesh 3D Import Panel"""
    bl_label = "Shadow Mesh 3D"
    bl_idname = "SHADOW_PT_import_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shadow Mesh'
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Import Settings:")
        layout.prop(context.scene, "shadow_obj_path")
        layout.prop(context.scene, "shadow_physics_path")
        
        layout.separator()
        layout.operator("shadow.import_mesh", text="Import Mesh")


class SHADOW_OT_import_mesh(bpy.types.Operator):
    """Import Shadow Mesh"""
    bl_idname = "shadow.import_mesh"
    bl_label = "Import Shadow Mesh"
    
    def execute(self, context):
        obj_path = context.scene.shadow_obj_path
        physics_path = context.scene.shadow_physics_path
        
        if not obj_path:
            self.report({'ERROR'}, "Please set OBJ file path")
            return {'CANCELLED'}
        
        try:
            import_obj_with_physics(obj_path, physics_path)
            self.report({'INFO'}, "Mesh imported successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}


def register():
    """Register Blender addon classes."""
    bpy.utils.register_class(SHADOW_PT_import_panel)
    bpy.utils.register_class(SHADOW_OT_import_mesh)
    
    bpy.types.Scene.shadow_obj_path = bpy.props.StringProperty(
        name="OBJ File",
        description="Path to OBJ file",
        default="",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.shadow_physics_path = bpy.props.StringProperty(
        name="Physics JSON",
        description="Path to physics JSON file",
        default="",
        subtype='FILE_PATH'
    )


def unregister():
    """Unregister Blender addon classes."""
    bpy.utils.unregister_class(SHADOW_PT_import_panel)
    bpy.utils.unregister_class(SHADOW_OT_import_mesh)
    
    del bpy.types.Scene.shadow_obj_path
    del bpy.types.Scene.shadow_physics_path


# Register when run as addon
if __name__ != "__main__":
    register()
