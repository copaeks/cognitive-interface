"""
API package for Shadow Intelligence Layer.
"""

from api.intelligence_api import (
    IntelligenceAPI,
    ShadowIntelligence,
    classify,
    quick_classify
)

__all__ = [
    'IntelligenceAPI',
    'ShadowIntelligence',
    'classify',
    'quick_classify'
]
