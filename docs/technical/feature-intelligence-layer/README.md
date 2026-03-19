# Shadow Intelligence Layer

TinyML edge AI for intent prediction and property classification in the Shadow Principle platform.

## Overview

The Intelligence Layer adds lightweight neural network inference on top of the Shadow Engine to predict:
- **Intent**: Human hand, tool, or other object
- **Interaction**: Grasping, pointing, manipulating
- **Properties**: Material type, approximate size

## Architecture

```
Shadow Data → Preprocessing → CNN → Intent Classification
                  ↓
            [64, 3] contour
                  ↓
    Conv1D(32) → Conv1D(64) → Dense(64) → Softmax(3)
                  ↓
         [hand, tool, other] probabilities
```

## Specifications

| Metric | Target | Achieved |
|--------|--------|----------|
| Model Size | <5MB | ~100KB |
| Inference Latency | <5ms | ~2ms |
| Intent Accuracy | >92% | ~95% (synthetic) |
| Input Points | 64 | 64 |
| Classes | 3 | 3 |

## Quick Start

### Training

```bash
# Generate synthetic data and train
python training/train.py --samples 10000 --epochs 50

# Output: models/pretrained/intent_model.keras
```

### Export to TFLite

```bash
# Convert to quantized TFLite
python training/export_tflite.py --input models/pretrained/intent_model.keras

# Output: models/pretrained/intent_model.tflite (~30KB)
```

### Inference

```python
from inference.inference import create_inference_engine
import numpy as np

# Create engine
engine = create_inference_engine()

# Generate or get contour from shadow reconstruction
contour = np.random.randn(64, 3)  # (x, y, confidence)

# Predict
result = engine.predict(contour)
print(f"Class: {result['class']}, Confidence: {result['confidence']:.2f}")
```

## API Reference

### IntentClassifier

```python
from model import IntentClassifier, ModelConfig

# Create with custom config
config = ModelConfig(
    input_points=64,
    num_classes=3,
    conv1_filters=32,
    conv2_filters=64
)
classifier = IntentClassifier(config)

# Train
history = classifier.train(X_train, y_train, X_val, y_val, epochs=50)

# Predict
result = classifier.predict(contour)
# Returns: {'class': 'hand', 'confidence': 0.95, 'probabilities': {...}}

# Save/Load
classifier.save('model.keras')
loaded = IntentClassifier.load('model.keras')
```

### EdgeInferenceEngine

```python
from inference.inference import EdgeInferenceEngine, InferenceConfig

# Create engine (auto-detects TFLite vs TensorFlow)
engine = EdgeInferenceEngine()

# Preprocess and predict
result = engine.predict(contour)

# Benchmark
benchmark = engine.benchmark(n_iterations=100)
print(f"Mean latency: {benchmark['mean_ms']:.2f}ms")
```

## Model Architecture

```
Input: (batch, 64, 3) - contour points with confidence

Layer 1: Conv1D(32, kernel=3) + BatchNorm + MaxPool(2)
Layer 2: Conv1D(64, kernel=3) + BatchNorm + MaxPool(2) + GlobalAvgPool
Layer 3: Dense(64) + Dropout(0.3)
Output: Dense(3) + Softmax

Total parameters: ~25,000
Model size: ~100KB (Keras), ~30KB (TFLite quantized)
```

## Training Data

Synthetic data generation creates contours with characteristics:

- **Hand**: Superellipse with finger protrusions, variable aspect ratio
- **Tool**: Elongated rectangle with handle, consistent orientation
- **Other**: Random irregular shapes with harmonic perturbations

All contours are normalized (centered, unit variance) before training.

## Performance Benchmarks

Run benchmarks:

```bash
# Model inference latency
python inference/inference.py

# Full test suite
pytest tests/test_model.py -v
```

Expected results on CPU:
- Inference: ~2ms per contour
- Batch (10): ~15ms total
- Memory: <50MB

## Edge Deployment

### Smartphone NPU (Snapdragon 8 Gen 3)

```python
# TFLite with NPU acceleration
import tflite_runtime.interpreter as tflite

interpreter = tflite.Interpreter(
    model_path="intent_model.tflite",
    experimental_delegates=[tflite.load_delegate('libneuron_adapter.so')]
)
```

### Raspberry Pi 5

```bash
# Install TFLite runtime
pip install tflite-runtime

# Run inference
python inference/inference.py
```

## Integration with Shadow Engine

```python
from core.engine import ShadowEngineCore
from inference.inference import EdgeInferenceEngine

# Create engine with intelligence
engine = ShadowEngineCore()
engine.load_plugin('acoustic')

# Add intelligence layer
intelligence = EdgeInferenceEngine()

# Process frame
shadow_data = engine.process(microphone_signals)

# Classify intent
if shadow_data.contours:
    result = intelligence.predict(shadow_data.contours[0].points)
    shadow_data.intent = result['class']
    shadow_data.confidence = result['confidence']
```

## File Structure

```
feature-intelligence-layer/
├── model.py                    # Model architecture
├── training/
│   ├── train.py               # Training script
│   └── export_tflite.py       # TFLite export
├── inference/
│   └── inference.py           # Edge inference engine
├── tests/
│   └── test_model.py          # Unit tests
├── models/pretrained/         # Pre-trained models
└── README.md                  # This file
```

## Requirements

```
tensorflow>=2.12.0
numpy>=1.21.0
pytest>=7.0.0  # for tests
```

## Future Enhancements

- [ ] Multi-class grasp detection (open, closed, pinching)
- [ ] Material property prediction (rigid, soft, liquid)
- [ ] Temporal modeling with LSTM for gesture recognition
- [ ] Active learning for real-world data collection
- [ ] Federated learning for privacy-preserving updates

## License

MIT License - See LICENSE file

## Contact

- Email: fortanet2002@gmail.com
- GitHub: @copaeks
