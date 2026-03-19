"""
Material Properties Database and Inference
==========================================

Comprehensive database of material physical properties for shadow-based
object reconstruction. Provides material lookup, interpolation, and
property estimation.

Author: Iván Vankov Fortanet
Email: fortanet2002@gmail.com
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class MaterialCategory(Enum):
    """Broad material categories."""
    METAL = "metal"
    CERAMIC = "ceramic"
    POLYMER = "polymer"
    COMPOSITE = "composite"
    BIOLOGICAL = "biological"
    FLUID = "fluid"
    GAS = "gas"
    OTHER = "other"


@dataclass
class MaterialProperties:
    """
    Complete physical properties for a material.
    
    All values in SI units unless otherwise specified.
    """
    # Identification
    name: str
    category: MaterialCategory
    
    # Mechanical properties
    density: float  # kg/m³
    youngs_modulus: float  # Pa
    poisson_ratio: float  # dimensionless
    shear_modulus: float  # Pa
    bulk_modulus: float  # Pa
    
    # Strength properties
    yield_strength: float  # Pa
    ultimate_strength: float  # Pa
    fracture_toughness: float  # MPa·√m
    
    # Thermal properties
    thermal_conductivity: float  # W/(m·K)
    specific_heat: float  # J/(kg·K)
    thermal_expansion: float  # 1/K
    melting_point: float  # K
    
    # Electrical properties
    electrical_conductivity: float  # S/m
    dielectric_constant: float  # dimensionless
    
    # Acoustic properties
    acoustic_impedance: float  # Pa·s/m
    sound_velocity: float  # m/s
    
    # Surface properties
    friction_coefficient_static: float
    friction_coefficient_kinetic: float
    surface_roughness_ra: float  # μm
    
    # Optical properties
    refractive_index: float
    opacity: float  # 0-1
    
    # Derived properties
    hardness_brinell: float  # HB
    hardness_vickers: float  # HV
    
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'category': self.category.value,
            'density_kg_m3': self.density,
            'youngs_modulus_pa': self.youngs_modulus,
            'poisson_ratio': self.poisson_ratio,
            'shear_modulus_pa': self.shear_modulus,
            'bulk_modulus_pa': self.bulk_modulus,
            'yield_strength_pa': self.yield_strength,
            'ultimate_strength_pa': self.ultimate_strength,
            'fracture_toughness_mpa_sqrt_m': self.fracture_toughness,
            'thermal_conductivity_w_m_k': self.thermal_conductivity,
            'specific_heat_j_kg_k': self.specific_heat,
            'thermal_expansion_1_k': self.thermal_expansion,
            'melting_point_k': self.melting_point,
            'electrical_conductivity_s_m': self.electrical_conductivity,
            'dielectric_constant': self.dielectric_constant,
            'acoustic_impedance_pa_s_m': self.acoustic_impedance,
            'sound_velocity_m_s': self.sound_velocity,
            'friction_coefficient_static': self.friction_coefficient_static,
            'friction_coefficient_kinetic': self.friction_coefficient_kinetic,
            'surface_roughness_ra_um': self.surface_roughness_ra,
            'refractive_index': self.refractive_index,
            'opacity': self.opacity,
            'hardness_brinell': self.hardness_brinell,
            'hardness_vickers': self.hardness_vickers,
            'description': self.description,
            'tags': self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialProperties':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            category=MaterialCategory(data.get('category', 'other')),
            density=data.get('density_kg_m3', 1000.0),
            youngs_modulus=data.get('youngs_modulus_pa', 1e9),
            poisson_ratio=data.get('poisson_ratio', 0.3),
            shear_modulus=data.get('shear_modulus_pa', 0.4e9),
            bulk_modulus=data.get('bulk_modulus_pa', 1.5e9),
            yield_strength=data.get('yield_strength_pa', 50e6),
            ultimate_strength=data.get('ultimate_strength_pa', 100e6),
            fracture_toughness=data.get('fracture_toughness_mpa_sqrt_m', 50.0),
            thermal_conductivity=data.get('thermal_conductivity_w_m_k', 1.0),
            specific_heat=data.get('specific_heat_j_kg_k', 1000.0),
            thermal_expansion=data.get('thermal_expansion_1_k', 1e-5),
            melting_point=data.get('melting_point_k', 300.0),
            electrical_conductivity=data.get('electrical_conductivity_s_m', 0.0),
            dielectric_constant=data.get('dielectric_constant', 1.0),
            acoustic_impedance=data.get('acoustic_impedance_pa_s_m', 1.5e6),
            sound_velocity=data.get('sound_velocity_m_s', 343.0),
            friction_coefficient_static=data.get('friction_coefficient_static', 0.3),
            friction_coefficient_kinetic=data.get('friction_coefficient_kinetic', 0.2),
            surface_roughness_ra=data.get('surface_roughness_ra_um', 1.0),
            refractive_index=data.get('refractive_index', 1.0),
            opacity=data.get('opacity', 1.0),
            hardness_brinell=data.get('hardness_brinell', 100.0),
            hardness_vickers=data.get('hardness_vickers', 100.0),
            description=data.get('description', ''),
            tags=data.get('tags', []),
        )
    
    def compute_derived_properties(self) -> Dict[str, float]:
        """Compute derived material properties."""
        # Wave velocity (longitudinal)
        vl = np.sqrt(self.youngs_modulus * (1 - self.poisson_ratio) / 
                     (self.density * (1 + self.poisson_ratio) * (1 - 2 * self.poisson_ratio)))
        
        # Shear wave velocity
        vs = np.sqrt(self.shear_modulus / self.density)
        
        # Rayleigh wave velocity (approximate)
        vr = vs * 0.9
        
        # Specific stiffness
        specific_stiffness = self.youngs_modulus / self.density
        
        # Acoustic impedance (if not set)
        if self.acoustic_impedance == 0:
            z = self.density * vl
        else:
            z = self.acoustic_impedance
        
        return {
            'longitudinal_wave_velocity': float(vl),
            'shear_wave_velocity': float(vs),
            'rayleigh_wave_velocity': float(vr),
            'specific_stiffness': float(specific_stiffness),
            'acoustic_impedance': float(z),
        }


class MaterialDatabase:
    """
    Database of material properties for physics inference.
    
    Provides fast lookup, interpolation, and similarity search.
    """
    
    def __init__(self):
        """Initialize material database with common materials."""
        self._materials: Dict[str, MaterialProperties] = {}
        self._category_index: Dict[MaterialCategory, List[str]] = {
            cat: [] for cat in MaterialCategory
        }
        self._build_database()
    
    def _build_database(self) -> None:
        """Build the material database."""
        materials = [
            # Metals
            MaterialProperties(
                name="aluminum_6061",
                category=MaterialCategory.METAL,
                density=2700.0,
                youngs_modulus=68.9e9,
                poisson_ratio=0.33,
                shear_modulus=26.0e9,
                bulk_modulus=76.0e9,
                yield_strength=276e6,
                ultimate_strength=310e6,
                fracture_toughness=29.0,
                thermal_conductivity=167.0,
                specific_heat=896.0,
                thermal_expansion=23.6e-6,
                melting_point=855.0,
                electrical_conductivity=25.0e6,
                dielectric_constant=1.0,
                acoustic_impedance=17.0e6,
                sound_velocity=6320.0,
                friction_coefficient_static=0.4,
                friction_coefficient_kinetic=0.3,
                surface_roughness_ra=0.8,
                refractive_index=1.44,
                opacity=1.0,
                hardness_brinell=95.0,
                hardness_vickers=107.0,
                description="Common aluminum alloy, lightweight and corrosion resistant",
                tags=["metal", "aluminum", "lightweight", "common"],
            ),
            MaterialProperties(
                name="steel_mild",
                category=MaterialCategory.METAL,
                density=7850.0,
                youngs_modulus=200.0e9,
                poisson_ratio=0.29,
                shear_modulus=79.0e9,
                bulk_modulus=140.0e9,
                yield_strength=250e6,
                ultimate_strength=400e6,
                fracture_toughness=50.0,
                thermal_conductivity=50.0,
                specific_heat=490.0,
                thermal_expansion=12.0e-6,
                melting_point=1773.0,
                electrical_conductivity=6.0e6,
                dielectric_constant=1.0,
                acoustic_impedance=39.0e6,
                sound_velocity=5960.0,
                friction_coefficient_static=0.6,
                friction_coefficient_kinetic=0.4,
                surface_roughness_ra=1.6,
                refractive_index=2.5,
                opacity=1.0,
                hardness_brinell=120.0,
                hardness_vickers=130.0,
                description="Mild carbon steel, common structural material",
                tags=["metal", "steel", "common", "structural"],
            ),
            MaterialProperties(
                name="copper_pure",
                category=MaterialCategory.METAL,
                density=8960.0,
                youngs_modulus=110.0e9,
                poisson_ratio=0.34,
                shear_modulus=48.0e9,
                bulk_modulus=140.0e9,
                yield_strength=70e6,
                ultimate_strength=220e6,
                fracture_toughness=65.0,
                thermal_conductivity=401.0,
                specific_heat=385.0,
                thermal_expansion=16.5e-6,
                melting_point=1358.0,
                electrical_conductivity=59.6e6,
                dielectric_constant=1.0,
                acoustic_impedance=41.6e6,
                sound_velocity=4600.0,
                friction_coefficient_static=0.5,
                friction_coefficient_kinetic=0.4,
                surface_roughness_ra=0.4,
                refractive_index=0.5,
                opacity=1.0,
                hardness_brinell=40.0,
                hardness_vickers=50.0,
                description="Pure copper, excellent electrical and thermal conductor",
                tags=["metal", "copper", "conductor"],
            ),
            # Ceramics
            MaterialProperties(
                name="alumina_ceramic",
                category=MaterialCategory.CERAMIC,
                density=3960.0,
                youngs_modulus=380.0e9,
                poisson_ratio=0.22,
                shear_modulus=155.0e9,
                bulk_modulus=230.0e9,
                yield_strength=300e6,
                ultimate_strength=300e6,
                fracture_toughness=4.0,
                thermal_conductivity=35.0,
                specific_heat=880.0,
                thermal_expansion=8.0e-6,
                melting_point=2323.0,
                electrical_conductivity=1e-12,
                dielectric_constant=9.8,
                acoustic_impedance=36.0e6,
                sound_velocity=10800.0,
                friction_coefficient_static=0.4,
                friction_coefficient_kinetic=0.3,
                surface_roughness_ra=0.1,
                refractive_index=1.76,
                opacity=0.0,
                hardness_brinell=2000.0,
                hardness_vickers=2200.0,
                description="Aluminum oxide ceramic, very hard and wear resistant",
                tags=["ceramic", "oxide", "hard", "transparent"],
            ),
            # Polymers
            MaterialProperties(
                name="abs_plastic",
                category=MaterialCategory.POLYMER,
                density=1050.0,
                youngs_modulus=2.3e9,
                poisson_ratio=0.35,
                shear_modulus=0.85e9,
                bulk_modulus=2.5e9,
                yield_strength=45e6,
                ultimate_strength=45e6,
                fracture_toughness=2.5,
                thermal_conductivity=0.15,
                specific_heat=1470.0,
                thermal_expansion=90.0e-6,
                melting_point=380.0,
                electrical_conductivity=1e-15,
                dielectric_constant=2.8,
                acoustic_impedance=2.3e6,
                sound_velocity=2200.0,
                friction_coefficient_static=0.4,
                friction_coefficient_kinetic=0.3,
                surface_roughness_ra=0.5,
                refractive_index=1.52,
                opacity=1.0,
                hardness_brinell=100.0,
                hardness_vickers=110.0,
                description="ABS plastic, common engineering thermoplastic",
                tags=["polymer", "plastic", "common", "3d_printing"],
            ),
            MaterialProperties(
                name="pla_plastic",
                category=MaterialCategory.POLYMER,
                density=1250.0,
                youngs_modulus=3.5e9,
                poisson_ratio=0.36,
                shear_modulus=1.3e9,
                bulk_modulus=3.9e9,
                yield_strength=60e6,
                ultimate_strength=60e6,
                fracture_toughness=2.8,
                thermal_conductivity=0.13,
                specific_heat=1800.0,
                thermal_expansion=70.0e-6,
                melting_point=423.0,
                electrical_conductivity=1e-15,
                dielectric_constant=2.7,
                acoustic_impedance=2.9e6,
                sound_velocity=2300.0,
                friction_coefficient_static=0.35,
                friction_coefficient_kinetic=0.25,
                surface_roughness_ra=0.6,
                refractive_index=1.46,
                opacity=1.0,
                hardness_brinell=80.0,
                hardness_vickers=90.0,
                description="PLA biodegradable plastic, popular for 3D printing",
                tags=["polymer", "plastic", "biodegradable", "3d_printing"],
            ),
            MaterialProperties(
                name="silicone_rubber",
                category=MaterialCategory.POLYMER,
                density=1100.0,
                youngs_modulus=0.01e9,
                poisson_ratio=0.49,
                shear_modulus=0.003e9,
                bulk_modulus=1.5e9,
                yield_strength=5e6,
                ultimate_strength=10e6,
                fracture_toughness=0.5,
                thermal_conductivity=0.2,
                specific_heat=1500.0,
                thermal_expansion=250.0e-6,
                melting_point=473.0,
                electrical_conductivity=1e-14,
                dielectric_constant=3.0,
                acoustic_impedance=1.8e6,
                sound_velocity=1000.0,
                friction_coefficient_static=0.8,
                friction_coefficient_kinetic=0.6,
                surface_roughness_ra=2.0,
                refractive_index=1.41,
                opacity=1.0,
                hardness_brinell=10.0,
                hardness_vickers=15.0,
                description="Silicone rubber, flexible and temperature resistant",
                tags=["polymer", "rubber", "flexible", "soft"],
            ),
            # Fluids
            MaterialProperties(
                name="water_pure",
                category=MaterialCategory.FLUID,
                density=1000.0,
                youngs_modulus=2.2e9,  # Bulk modulus
                poisson_ratio=0.5,
                shear_modulus=0.0,
                bulk_modulus=2.2e9,
                yield_strength=0.0,
                ultimate_strength=0.0,
                fracture_toughness=0.0,
                thermal_conductivity=0.6,
                specific_heat=4186.0,
                thermal_expansion=210.0e-6,
                melting_point=273.0,
                electrical_conductivity=5.5e-6,
                dielectric_constant=80.0,
                acoustic_impedance=1.48e6,
                sound_velocity=1480.0,
                friction_coefficient_static=0.0,
                friction_coefficient_kinetic=0.0,
                surface_roughness_ra=0.0,
                refractive_index=1.33,
                opacity=0.0,
                hardness_brinell=0.0,
                hardness_vickers=0.0,
                description="Pure water at 20°C",
                tags=["fluid", "liquid", "water", "common"],
            ),
            MaterialProperties(
                name="air",
                category=MaterialCategory.GAS,
                density=1.225,
                youngs_modulus=101325.0,  # Atmospheric pressure
                poisson_ratio=0.0,
                shear_modulus=0.0,
                bulk_modulus=101325.0,
                yield_strength=0.0,
                ultimate_strength=0.0,
                fracture_toughness=0.0,
                thermal_conductivity=0.026,
                specific_heat=1005.0,
                thermal_expansion=3.43e-3,
                melting_point=0.0,
                electrical_conductivity=0.0,
                dielectric_constant=1.0,
                acoustic_impedance=415.0,
                sound_velocity=343.0,
                friction_coefficient_static=0.0,
                friction_coefficient_kinetic=0.0,
                surface_roughness_ra=0.0,
                refractive_index=1.0003,
                opacity=0.0,
                hardness_brinell=0.0,
                hardness_vickers=0.0,
                description="Air at 20°C and 1 atm",
                tags=["gas", "air", "common"],
            ),
            # Biological
            MaterialProperties(
                name="human_skin",
                category=MaterialCategory.BIOLOGICAL,
                density=1100.0,
                youngs_modulus=0.5e6,
                poisson_ratio=0.49,
                shear_modulus=0.17e6,
                bulk_modulus=2.0e9,
                yield_strength=10e6,
                ultimate_strength=20e6,
                fracture_toughness=1.0,
                thermal_conductivity=0.3,
                specific_heat=3500.0,
                thermal_expansion=100.0e-6,
                melting_point=373.0,
                electrical_conductivity=0.001,
                dielectric_constant=50.0,
                acoustic_impedance=1.6e6,
                sound_velocity=1540.0,
                friction_coefficient_static=0.6,
                friction_coefficient_kinetic=0.4,
                surface_roughness_ra=10.0,
                refractive_index=1.4,
                opacity=1.0,
                hardness_brinell=5.0,
                hardness_vickers=8.0,
                description="Human skin tissue",
                tags=["biological", "tissue", "soft"],
            ),
            MaterialProperties(
                name="human_bone_cortical",
                category=MaterialCategory.BIOLOGICAL,
                density=1900.0,
                youngs_modulus=17.0e9,
                poisson_ratio=0.3,
                shear_modulus=6.5e9,
                bulk_modulus=14.0e9,
                yield_strength=120e6,
                ultimate_strength=160e6,
                fracture_toughness=4.0,
                thermal_conductivity=0.5,
                specific_heat=1300.0,
                thermal_expansion=8.0e-6,
                melting_point=373.0,
                electrical_conductivity=0.01,
                dielectric_constant=10.0,
                acoustic_impedance=4.0e6,
                sound_velocity=3500.0,
                friction_coefficient_static=0.3,
                friction_coefficient_kinetic=0.2,
                surface_roughness_ra=5.0,
                refractive_index=1.56,
                opacity=1.0,
                hardness_brinell=80.0,
                hardness_vickers=100.0,
                description="Cortical (compact) bone",
                tags=["biological", "bone", "rigid"],
            ),
        ]
        
        for material in materials:
            self.add_material(material)
    
    def add_material(self, material: MaterialProperties) -> None:
        """Add a material to the database."""
        self._materials[material.name] = material
        self._category_index[material.category].append(material.name)
    
    def get_material(self, name: str) -> Optional[MaterialProperties]:
        """Get material by name."""
        return self._materials.get(name)
    
    def find_by_category(self, category: MaterialCategory) -> List[MaterialProperties]:
        """Find all materials in a category."""
        names = self._category_index.get(category, [])
        return [self._materials[name] for name in names if name in self._materials]
    
    def search_by_tags(self, tags: List[str]) -> List[MaterialProperties]:
        """Search materials by tags."""
        results = []
        for material in self._materials.values():
            if any(tag in material.tags for tag in tags):
                results.append(material)
        return results
    
    def find_similar(
        self,
        density: float,
        youngs_modulus: float,
        n_results: int = 3,
    ) -> List[Tuple[MaterialProperties, float]]:
        """
        Find materials similar to given properties.
        
        Args:
            density: Target density in kg/m³
            youngs_modulus: Target Young's modulus in Pa
            n_results: Number of results to return
            
        Returns:
            List of (material, similarity_score) tuples
        """
        scores = []
        
        for material in self._materials.values():
            # Normalize differences
            density_diff = abs(material.density - density) / max(density, 100)
            modulus_diff = abs(material.youngs_modulus - youngs_modulus) / max(youngs_modulus, 1e6)
            
            # Combined score (lower is better)
            score = density_diff + modulus_diff
            similarity = 1.0 / (1.0 + score)
            
            scores.append((material, similarity))
        
        # Sort by similarity (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:n_results]
    
    def interpolate_properties(
        self,
        material1: str,
        material2: str,
        t: float,
    ) -> MaterialProperties:
        """
        Interpolate between two materials.
        
        Args:
            material1: First material name
            material2: Second material name
            t: Interpolation factor (0.0 = material1, 1.0 = material2)
            
        Returns:
            Interpolated material properties
        """
        m1 = self._materials.get(material1)
        m2 = self._materials.get(material2)
        
        if m1 is None or m2 is None:
            raise ValueError(f"Material not found: {material1} or {material2}")
        
        t = np.clip(t, 0.0, 1.0)
        
        def lerp(a: float, b: float, t: float) -> float:
            return a * (1 - t) + b * t
        
        return MaterialProperties(
            name=f"{m1.name}_{m2.name}_blend_{t:.2f}",
            category=m1.category if t < 0.5 else m2.category,
            density=lerp(m1.density, m2.density, t),
            youngs_modulus=lerp(m1.youngs_modulus, m2.youngs_modulus, t),
            poisson_ratio=lerp(m1.poisson_ratio, m2.poisson_ratio, t),
            shear_modulus=lerp(m1.shear_modulus, m2.shear_modulus, t),
            bulk_modulus=lerp(m1.bulk_modulus, m2.bulk_modulus, t),
            yield_strength=lerp(m1.yield_strength, m2.yield_strength, t),
            ultimate_strength=lerp(m1.ultimate_strength, m2.ultimate_strength, t),
            fracture_toughness=lerp(m1.fracture_toughness, m2.fracture_toughness, t),
            thermal_conductivity=lerp(m1.thermal_conductivity, m2.thermal_conductivity, t),
            specific_heat=lerp(m1.specific_heat, m2.specific_heat, t),
            thermal_expansion=lerp(m1.thermal_expansion, m2.thermal_expansion, t),
            melting_point=lerp(m1.melting_point, m2.melting_point, t),
            electrical_conductivity=lerp(m1.electrical_conductivity, m2.electrical_conductivity, t),
            dielectric_constant=lerp(m1.dielectric_constant, m2.dielectric_constant, t),
            acoustic_impedance=lerp(m1.acoustic_impedance, m2.acoustic_impedance, t),
            sound_velocity=lerp(m1.sound_velocity, m2.sound_velocity, t),
            friction_coefficient_static=lerp(m1.friction_coefficient_static, m2.friction_coefficient_static, t),
            friction_coefficient_kinetic=lerp(m1.friction_coefficient_kinetic, m2.friction_coefficient_kinetic, t),
            surface_roughness_ra=lerp(m1.surface_roughness_ra, m2.surface_roughness_ra, t),
            refractive_index=lerp(m1.refractive_index, m2.refractive_index, t),
            opacity=lerp(m1.opacity, m2.opacity, t),
            hardness_brinell=lerp(m1.hardness_brinell, m2.hardness_brinell, t),
            hardness_vickers=lerp(m1.hardness_vickers, m2.hardness_vickers, t),
            description=f"Blend of {m1.name} and {m2.name}",
            tags=list(set(m1.tags + m2.tags)),
        )
    
    def export_to_json(self, filepath: str) -> None:
        """Export database to JSON file."""
        data = {
            'materials': [m.to_dict() for m in self._materials.values()],
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filepath: str) -> None:
        """Import database from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for material_data in data.get('materials', []):
            material = MaterialProperties.from_dict(material_data)
            self.add_material(material)
    
    @property
    def material_names(self) -> List[str]:
        """Get list of all material names."""
        return list(self._materials.keys())
    
    @property
    def count(self) -> int:
        """Get number of materials in database."""
        return len(self._materials)


# Global database instance
_material_db: Optional[MaterialDatabase] = None


def get_material_database() -> MaterialDatabase:
    """Get global material database instance."""
    global _material_db
    if _material_db is None:
        _material_db = MaterialDatabase()
    return _material_db


def print_material_summary():
    """Print summary of material database."""
    db = get_material_database()
    
    print("=" * 60)
    print("MATERIAL DATABASE SUMMARY")
    print("=" * 60)
    print(f"\nTotal materials: {db.count}")
    
    print("\nBy category:")
    for category in MaterialCategory:
        materials = db.find_by_category(category)
        if materials:
            print(f"  {category.value}: {len(materials)} materials")
            for m in materials:
                print(f"    - {m.name}: ρ={m.density:.0f} kg/m³, E={m.youngs_modulus/1e9:.1f} GPa")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_material_summary()
    
    # Demo similarity search
    db = get_material_database()
    print("\nSimilarity search example:")
    print("-" * 40)
    print("Finding materials similar to: density=1500 kg/m³, E=5 GPa")
    similar = db.find_similar(density=1500, youngs_modulus=5e9, n_results=3)
    for material, score in similar:
        print(f"  {material.name}: similarity={score:.3f}")
