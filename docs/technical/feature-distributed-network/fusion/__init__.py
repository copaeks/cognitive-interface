"""Fusion layer for multi-array shadow tracking."""

from .shadow_fusion import (
    Vector2D,
    ArrayPosition,
    ShadowObservation,
    ShadowFusionEngine,
    SpatialHash,
    TriangulationFusion,
    FusedShadow
)

from .global_map import (
    GlobalObject,
    GlobalShadowMap,
    ArrayCoverage,
    CoveragePlanner
)

__all__ = [
    # Shadow Fusion
    'Vector2D',
    'ArrayPosition',
    'ShadowObservation',
    'ShadowFusionEngine',
    'SpatialHash',
    'TriangulationFusion',
    'FusedShadow',
    # Global Map
    'GlobalObject',
    'GlobalShadowMap',
    'ArrayCoverage',
    'CoveragePlanner'
]
