"""
Inference package for Shadow Intelligence Layer.
"""

from inference.edge_inference import (
    EdgeInferenceEngine,
    InferenceMode,
    InferenceResult,
    create_edge_engine
)

# Import from standalone intent inference module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from intent_inference import (
    IntentClassifier,
    IntentType,
    IntentPrediction,
    predict_intent,
    preprocess_contour,
    batch_preprocess
)

__all__ = [
    'EdgeInferenceEngine',
    'InferenceMode',
    'InferenceResult',
    'create_edge_engine',
    'IntentClassifier',
    'IntentType',
    'IntentPrediction',
    'predict_intent',
    'preprocess_contour',
    'batch_preprocess'
]
