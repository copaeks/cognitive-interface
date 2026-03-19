"""
Unreal Engine Integration Example
=================================

This script demonstrates how to import Shadow Mesh 3D outputs into Unreal Engine 5.3+.
Run from Unreal Editor's Python console or as an Editor Utility Script.

Requirements:
    - Unreal Engine 5.3 or newer
    - Python Editor Script Plugin enabled
    - glTF Importer plugin enabled
    - Shadow Mesh 3D output files (.glb + .json)

Usage:
    1. Enable Python Editor Script Plugin
    2. Open Output Log (Window > Developer Tools > Output Log)
    3. Switch to Python mode
    4. Run this script

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

import unreal
import json
import os


# =============================================================================
# CONFIGURATION - Modify these paths
# =============================================================================

# Path to your exported files
GLB_FILE_PATH = "C:/path/to/your/model.glb"  # Change this!
PHYSICS_JSON_PATH = "C:/path/to/your/physics.json"  # Change this!

# Import destination in Content Browser
DESTINATION_PATH = "/Game/ShadowMeshes"

# Import options
CREATE_MATERIAL = True
SETUP_PHYSICS = True
CREATE_BLUEPRINT = False


# =============================================================================
# UTILITY FUNCTIONS
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
        unreal.log_warning(f"Physics file not found: {json_path}")
        return {}
    
    with open(json_path, 'r') as f:
        return json.load(f)


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure a Content Browser directory exists.
    
    Args:
        directory_path: Path like "/Game/ShadowMeshes"
        
    Returns:
        True if directory exists or was created
    """
    if unreal.EditorAssetLibrary.does_directory_exist(directory_path):
        return True
    
    # Try to create directory
    return unreal.EditorAssetLibrary.make_directory(directory_path)


def get_base_filename(filepath: str) -> str:
    """Get base filename without extension."""
    return os.path.splitext(os.path.basename(filepath))[0]


# =============================================================================
# IMPORT FUNCTIONS
# =============================================================================

def import_gltf_file(
    glb_path: str,
    destination_path: str,
    options: dict = None
) -> unreal.StaticMesh:
    """
    Import glTF/GLB file into Unreal Engine.
    
    Args:
        glb_path: Path to GLB file
        destination_path: Content Browser destination path
        options: Additional import options
        
    Returns:
        Imported StaticMesh asset
    """
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"GLB file not found: {glb_path}")
    
    # Ensure destination directory exists
    if not ensure_directory_exists(destination_path):
        raise RuntimeError(f"Failed to create directory: {destination_path}")
    
    # Setup import task
    task = unreal.AssetImportTask()
    task.filename = glb_path
    task.destination_path = destination_path
    task.destination_name = get_base_filename(glb_path)
    task.replace_existing = True
    task.automated = True
    task.save = True
    
    # Configure glTF import options
    gltf_options = unreal.GLTFImportOptions()
    gltf_options.import_mesh = True
    gltf_options.import_materials = True
    gltf_options.import_textures = True
    
    # Set options
    task.options = gltf_options
    
    # Import
    unreal.log(f"Importing: {glb_path}")
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    
    # Get imported asset
    asset_path = f"{destination_path}/{task.destination_name}"
    
    # Try to load as StaticMesh
    static_mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    
    if static_mesh is None:
        # Try with _StaticMesh suffix
        static_mesh = unreal.EditorAssetLibrary.load_asset(f"{asset_path}_StaticMesh")
    
    if static_mesh is None:
        raise RuntimeError(f"Failed to load imported asset: {asset_path}")
    
    unreal.log(f"Imported: {static_mesh.get_name()}")
    return static_mesh


def create_physical_material(physics: dict, name: str) -> unreal.PhysicalMaterial:
    """
    Create a PhysicalMaterial based on physics properties.
    
    Args:
        physics: Physics properties dictionary
        name: Material name
        
    Returns:
        Created PhysicalMaterial asset
    """
    # Create physical material
    phys_mat = unreal.PhysicalMaterial()
    
    # Set properties
    friction = physics.get('friction_coefficient', 0.5)
    restitution = physics.get('restitution', 0.5)
    density = physics.get('density_kg_m3', 1000.0)
    
    phys_mat.set_editor_property("friction", friction)
    phys_mat.set_editor_property("restitution", restitution)
    phys_mat.set_editor_property("density", density / 1000.0)  # Convert to g/cm³
    
    # Save asset
    asset_path = f"{DESTINATION_PATH}/PM_{name}"
    unreal.EditorAssetLibrary.save_loaded_asset(phys_mat, asset_path)
    
    unreal.log(f"Created physical material: {asset_path}")
    return phys_mat


def setup_static_mesh_physics(
    static_mesh: unreal.StaticMesh,
    physics: dict
) -> None:
    """
    Setup physics properties for StaticMesh.
    
    Args:
        static_mesh: StaticMesh asset
        physics: Physics properties dictionary
    """
    # Get body setup
    body_setup = static_mesh.get_editor_property("body_setup")
    
    if body_setup is None:
        unreal.log_warning("No body setup found, creating new one")
        body_setup = unreal.BodySetup()
        static_mesh.set_editor_property("body_setup", body_setup)
    
    # Set collision complexity
    body_setup.set_editor_property("collision_trace_flag", 
                                   unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    
    # Create physical material
    material_name = physics.get('material_type', 'default')
    phys_mat = create_physical_material(physics, material_name)
    
    # Apply physical material
    body_setup.set_editor_property("phys_material", phys_mat)
    
    # Set mass properties
    mass = physics.get('mass_kg', 1.0)
    body_setup.set_editor_property("mass_in_kg", mass)
    
    # Enable physics
    body_setup.set_editor_property("physics_type", unreal.BodyInstancePhysicsType.Simulated)
    
    unreal.log(f"Physics setup complete for {static_mesh.get_name()}")


def create_pbr_material(
    physics: dict,
    name: str,
    destination_path: str
) -> unreal.Material:
    """
    Create a PBR material based on physics properties.
    
    Args:
        physics: Physics properties dictionary
        name: Material name
        destination_path: Content Browser destination path
        
    Returns:
        Created Material asset
    """
    # Create material factory
    factory = unreal.MaterialFactoryNew()
    
    # Create material asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        f"M_{name}",
        destination_path,
        unreal.Material,
        factory
    )
    
    # Get material type and rigidity
    material_type = physics.get('material_type', 'unknown')
    rigidity = physics.get('rigidity', 0.5)
    
    # Material type colors (linear)
    type_colors = {
        'rigid_solid': (0.7, 0.72, 0.75, 1.0),
        'soft_solid': (0.95, 0.6, 0.4, 1.0),
        'liquid': (0.3, 0.5, 0.95, 0.8),
        'granular': (0.85, 0.75, 0.55, 1.0),
        'gas': (0.9, 0.95, 1.0, 0.3),
        'unknown': (0.5, 0.5, 0.5, 1.0),
    }
    
    base_color = type_colors.get(material_type, type_colors['unknown'])
    
    # Create constant nodes for PBR parameters
    # Base Color
    color_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant4Vector, -300, 0
    )
    color_node.set_editor_property("constant", unreal.LinearColor(
        base_color[0], base_color[1], base_color[2], base_color[3]
    ))
    
    # Metallic
    metallic_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 100
    )
    metallic_node.set_editor_property("r", rigidity * 0.8)
    
    # Roughness
    roughness_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 200
    )
    roughness_node.set_editor_property("r", 1.0 - rigidity * 0.7)
    
    # Specular
    specular_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 300
    )
    specular_node.set_editor_property("r", 0.5)
    
    # Connect nodes
    unreal.MaterialEditingLibrary.connect_material_property(
        color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic_node, "", unreal.MaterialProperty.MP_METALLIC
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        specular_node, "", unreal.MaterialProperty.MP_SPECULAR
    )
    
    # Set blend mode for transparent materials
    if material_type in ['liquid', 'gas']:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    
    # Recompile material
    unreal.MaterialEditingLibrary.recompile_material(material)
    
    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    
    unreal.log(f"Created material: {material.get_name()}")
    return material


def apply_material_to_mesh(
    static_mesh: unreal.StaticMesh,
    material: unreal.Material
) -> None:
    """
    Apply material to StaticMesh.
    
    Args:
        static_mesh: StaticMesh asset
        material: Material asset
    """
    # Get static mesh materials
    materials = static_mesh.get_editor_property("static_materials")
    
    if materials:
        # Replace first material
        materials[0].set_editor_property("material_interface", material)
    else:
        # Add new material
        static_mesh_material = unreal.StaticMaterial()
        static_mesh_material.set_editor_property("material_interface", material)
        materials.append(static_mesh_material)
    
    static_mesh.set_editor_property("static_materials", materials)
    
    unreal.log(f"Applied material {material.get_name()} to {static_mesh.get_name()}")


def create_blueprint_from_mesh(
    static_mesh: unreal.StaticMesh,
    physics: dict,
    destination_path: str
) -> unreal.Blueprint:
    """
    Create a Blueprint from StaticMesh with physics setup.
    
    Args:
        static_mesh: StaticMesh asset
        physics: Physics properties dictionary
        destination_path: Content Browser destination path
        
    Returns:
        Created Blueprint asset
    """
    # Create blueprint factory
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    
    # Create blueprint
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    blueprint = asset_tools.create_asset(
        f"BP_{static_mesh.get_name()}",
        destination_path,
        unreal.Blueprint,
        factory
    )
    
    # Get blueprint class
    bp_class = blueprint.generated_class()
    
    # Get default object
    cd_o = bp_class.get_default_object()
    
    # Add static mesh component
    mesh_component = unreal.StaticMeshComponent()
    mesh_component.set_editor_property("static_mesh", static_mesh)
    
    # Set physics properties
    mesh_component.set_editor_property("simulate_physics", True)
    mesh_component.set_editor_property("enable_gravity", True)
    
    # Set mass
    mass = physics.get('mass_kg', 1.0)
    mesh_component.set_editor_property("mass_scale", mass)
    
    # Add component to blueprint
    cd_o.add_instance_component(mesh_component)
    
    # Set root component
    cd_o.set_editor_property("root_component", mesh_component)
    
    # Compile and save
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    
    unreal.log(f"Created blueprint: {blueprint.get_name()}")
    return blueprint


def spawn_actor_in_level(
    static_mesh: unreal.StaticMesh,
    location: unreal.Vector = None,
    rotation: unreal.Rotator = None
) -> unreal.Actor:
    """
    Spawn an actor with the StaticMesh in the current level.
    
    Args:
        static_mesh: StaticMesh asset
        location: Spawn location
        rotation: Spawn rotation
        
    Returns:
        Spawned Actor
    """
    if location is None:
        location = unreal.Vector(0, 0, 100)
    
    if rotation is None:
        rotation = unreal.Rotator(0, 0, 0)
    
    # Get editor world
    editor_world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Spawn actor
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        static_mesh,
        location,
        rotation
    )
    
    if actor:
        unreal.log(f"Spawned actor: {actor.get_name()}")
    
    return actor


# =============================================================================
# BATCH IMPORT
# =============================================================================

def batch_import_directory(
    directory: str,
    destination_path: str = DESTINATION_PATH,
    pattern: str = "*.glb"
) -> list:
    """
    Import all GLB files in a directory.
    
    Args:
        directory: Directory containing GLB files
        destination_path: Content Browser destination path
        pattern: File pattern to match
        
    Returns:
        List of imported StaticMesh assets
    """
    import glob
    
    glb_files = glob.glob(os.path.join(directory, pattern))
    
    unreal.log(f"Found {len(glb_files)} GLB files in {directory}")
    
    imported_meshes = []
    
    for glb_path in glb_files:
        # Look for corresponding physics file
        base_name = os.path.splitext(glb_path)[0]
        physics_path = base_name + "_physics.json"
        
        if not os.path.exists(physics_path):
            physics_path = None
        
        try:
            # Import mesh
            static_mesh = import_gltf_file(glb_path, destination_path)
            
            # Load physics
            if physics_path:
                physics = load_physics_properties(physics_path)
                
                # Setup physics
                setup_static_mesh_physics(static_mesh, physics)
                
                # Create and apply material
                if CREATE_MATERIAL:
                    material = create_pbr_material(
                        physics,
                        get_base_filename(glb_path),
                        destination_path
                    )
                    apply_material_to_mesh(static_mesh, material)
            
            imported_meshes.append(static_mesh)
            
        except Exception as e:
            unreal.log_error(f"Error importing {glb_path}: {e}")
    
    unreal.log(f"Successfully imported {len(imported_meshes)} meshes")
    return imported_meshes


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    unreal.log("=" * 60)
    unreal.log("SHADOW MESH 3D - UNREAL ENGINE IMPORT")
    unreal.log("=" * 60)
    
    # Check if paths are set
    if GLB_FILE_PATH == "C:/path/to/your/model.glb":
        unreal.log_error("Please set GLB_FILE_PATH and PHYSICS_JSON_PATH")
        unreal.log("Edit the CONFIGURATION section at the top of this script")
        return
    
    try:
        # Import the mesh
        static_mesh = import_gltf_file(GLB_FILE_PATH, DESTINATION_PATH)
        
        # Load physics properties
        physics = load_physics_properties(PHYSICS_JSON_PATH)
        
        if physics:
            # Setup physics
            if SETUP_PHYSICS:
                setup_static_mesh_physics(static_mesh, physics)
            
            # Create and apply material
            if CREATE_MATERIAL:
                material = create_pbr_material(
                    physics,
                    get_base_filename(GLB_FILE_PATH),
                    DESTINATION_PATH
                )
                apply_material_to_mesh(static_mesh, material)
            
            # Create blueprint
            if CREATE_BLUEPRINT:
                blueprint = create_blueprint_from_mesh(
                    static_mesh,
                    physics,
                    DESTINATION_PATH
                )
        
        # Spawn in level (optional)
        # spawn_actor_in_level(static_mesh)
        
        unreal.log("=" * 60)
        unreal.log("IMPORT COMPLETE")
        unreal.log("=" * 60)
        unreal.log(f"Static Mesh: {static_mesh.get_name()}")
        unreal.log(f"Location: {DESTINATION_PATH}")
        
    except Exception as e:
        unreal.log_error(f"Import failed: {e}")
        import traceback
        traceback.print_exc()


# Run main function
if __name__ == "__main__":
    main()


# =============================================================================
# EDITOR UTILITY WIDGET (Optional)
# =============================================================================

class ShadowMeshImporter:
    """Editor utility class for importing Shadow Mesh files."""
    
    @staticmethod
    def import_single(glb_path: str, physics_path: str = None) -> unreal.StaticMesh:
        """Import a single GLB file."""
        static_mesh = import_gltf_file(glb_path, DESTINATION_PATH)
        
        if physics_path and os.path.exists(physics_path):
            physics = load_physics_properties(physics_path)
            setup_static_mesh_physics(static_mesh, physics)
        
        return static_mesh
    
    @staticmethod
    def import_directory(directory: str) -> list:
        """Import all GLB files in a directory."""
        return batch_import_directory(directory, DESTINATION_PATH)


# Example usage in Unreal Python console:
# import example_unreal_export
# example_unreal_export.main()
# 
# Or use the utility class:
# importer = example_unreal_export.ShadowMeshImporter()
# mesh = importer.import_single("C:/models/hand.glb", "C:/models/hand_physics.json")
