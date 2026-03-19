# Shadow Intelligence Layer - Dependencies
# ==========================================

# Core dependencies
tensorflow>=2.15.0
numpy>=1.24.0

# Optional: TFLite runtime for edge deployment (lighter than full TF)
# tflite-runtime>=2.15.0

# Development dependencies
pytest>=7.4.0
pytest-cov>=4.1.0

# Type checking (optional)
# mypy>=1.7.0
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
"""
Shadow Intelligence Layer - Training Script
============================================

Training pipeline for intent classification model using synthetic data.
Generates labeled shadow contours for hand, tool, and other categories.

Author: Cognitive AR Empire 2035 Technical Team
Version: 1.0
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Tuple, Optional, Dict, List
import os
import json
from datetime import datetime
import argparse

from model import (
    create_intent_classifier,
    ModelConfig,
    preprocess_contour,
    save_model,
    estimate_model_size_mb
)


# =============================================================================
# SYNTHETIC DATA GENERATION
# =============================================================================

class SyntheticDataGenerator:
    """Generate synthetic shadow contours for training"""
    
    def __init__(self, contour_points: int = ModelConfig.CONTOUR_POINTS, seed: int = 42):
        self.contour_points = contour_points
        self.rng = np.random.RandomState(seed)
    
    def generate_hand_contour(
        self,
        position: Optional[np.ndarray] = None,
        orientation: Optional[float] = None,
        finger_spread: float = 0.3,
        noise_level: float = 0.01
    ) -> np.ndarray:
        """
        Generate a synthetic hand contour.
        
        Hand shape: palm + 5 fingers with characteristic spacing.
        """
        # Default position and orientation
        if position is None:
            position = self.rng.randn(2) * 0.05
        if orientation is None:
            orientation = self.rng.uniform(0, 2 * np.pi)
        
        # Hand parameters (normalized units)
        palm_width = 0.08
        palm_height = 0.10
        finger_length = 0.08
        finger_width = 0.015
        
        # Create palm (rectangle)
        palm_points = []
        n_palm = self.contour_points // 3
        for i in range(n_palm):
            t = i / n_palm
            angle = 2 * np.pi * t
            # Rounded rectangle
            x = palm_width * np.cos(angle) * 0.7
            y = palm_height * np.sin(angle) * 0.8
            palm_points.append([x, y])
        
        # Create fingers
        finger_points = []
        n_fingers = 5
        n_per_finger = (self.contour_points - n_palm) // n_fingers
        
        for finger_idx in range(n_fingers):
            # Finger base position on palm edge
            base_x = palm_width * 0.6
            base_y = (finger_idx - 2) * palm_height * 0.25 * (1 + finger_spread)
            
            # Finger direction (slight spread)
            finger_angle = (finger_idx - 2) * 0.15
            
            for j in range(n_per_finger):
                t = j / n_per_finger
                # Tapered finger shape
                width = finger_width * (1 - t * 0.5)
                fx = base_x + t * finger_length * np.cos(finger_angle)
                fy = base_y + t * finger_length * np.sin(finger_angle) * 0.3 + width * np.sin(t * np.pi)
                finger_points.append([fx, fy])
        
        # Combine and convert to array
        contour = np.array(palm_points + finger_points)
        
        # Rotate by orientation
        cos_o, sin_o = np.cos(orientation), np.sin(orientation)
        rotation = np.array([[cos_o, -sin_o], [sin_o, cos_o]])
        contour = (rotation @ contour.T).T
        
        # Translate to position
        contour = contour + position
        
        # Add noise
        contour += self.rng.randn(*contour.shape) * noise_level
        
        # Ensure we have exactly contour_points
        if len(contour) > self.contour_points:
            indices = np.linspace(0, len(contour) - 1, self.contour_points, dtype=int)
            contour = contour[indices]
        elif len(contour) < self.contour_points:
            # Pad by interpolation
            padded = np.zeros((self.contour_points, 2))
            for i in range(2):
                padded[:, i] = np.interp(
                    np.linspace(0, len(contour) - 1, self.contour_points),
                    np.arange(len(contour)),
                    contour[:, i]
                )
            contour = padded
        
        return contour.astype(np.float32)
    
    def generate_tool_contour(
        self,
        tool_type: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[float] = None,
        noise_level: float = 0.005
    ) -> np.ndarray:
        """
        Generate a synthetic tool contour.
        
        Tool types: 'screwdriver', 'wrench', 'pliers', 'hammer'
        Tools have more regular, rigid shapes compared to hands.
        """
        if tool_type is None:
            tool_type = self.rng.choice(['screwdriver', 'wrench', 'pliers', 'hammer'])
        if position is None:
            position = self.rng.randn(2) * 0.05
        if orientation is None:
            orientation = self.rng.uniform(0, 2 * np.pi)
        
        contour = []
        
        if tool_type == 'screwdriver':
            # Long thin handle + tip
            length = 0.15
            width = 0.015
            for i in range(self.contour_points):
                t = i / self.contour_points
                # Rectangular shape
                x = length * (t - 0.5)
                y = width * np.sin(2 * np.pi * t * 2) * 0.3  # Slight variation
                contour.append([x, y])
        
        elif tool_type == 'wrench':
            # Handle with C-shaped head
            handle_length = 0.12
            handle_width = 0.02
            for i in range(self.contour_points):
                t = i / self.contour_points
                if t < 0.7:  # Handle
                    x = handle_length * (t / 0.7 - 0.5)
                    y = handle_width * 0.5 * np.sin(2 * np.pi * t * 3)
                else:  # C-shaped head
                    angle = (t - 0.7) / 0.3 * 2 * np.pi
                    x = handle_length * 0.3 + 0.04 * np.cos(angle)
                    y = 0.04 * np.sin(angle)
                contour.append([x, y])
        
        elif tool_type == 'pliers':
            # Two arms meeting at pivot
            for i in range(self.contour_points):
                t = i / self.contour_points
                if t < 0.4:  # First arm
                    angle = np.pi * 0.7 + t / 0.4 * np.pi * 0.3
                    r = 0.08 + 0.05 * (t / 0.4)
                    x = r * np.cos(angle)
                    y = r * np.sin(angle)
                elif t < 0.5:  # Pivot area
                    angle = np.pi * 0.5
                    r = 0.02
                    x = r * np.cos(angle + (t - 0.4) * 10)
                    y = r * np.sin(angle + (t - 0.4) * 10)
                else:  # Second arm
                    angle = np.pi * 0.3 + (t - 0.5) / 0.5 * np.pi * 0.3
                    r = 0.08 + 0.05 * ((t - 0.5) / 0.5)
                    x = r * np.cos(angle)
                    y = r * np.sin(angle)
                contour.append([x, y])
        
        else:  # hammer or default
            # Rectangular head + handle
            for i in range(self.contour_points):
                t = i / self.contour_points
                if t < 0.3:  # Hammer head
                    x = 0.06 * np.cos(2 * np.pi * t / 0.3)
                    y = 0.03 * np.sin(2 * np.pi * t / 0.3)
                else:  # Handle
                    x = 0.08 + 0.10 * ((t - 0.3) / 0.7)
                    y = 0.015 * np.sin(2 * np.pi * (t - 0.3) * 5)
                contour.append([x, y])
        
        contour = np.array(contour)
        
        # Rotate
        cos_o, sin_o = np.cos(orientation), np.sin(orientation)
        rotation = np.array([[cos_o, -sin_o], [sin_o, cos_o]])
        contour = (rotation @ contour.T).T
        
        # Translate
        contour = contour + position
        
        # Add noise (less than hand for rigid tool)
        contour += self.rng.randn(*contour.shape) * noise_level
        
        return contour.astype(np.float32)
    
    def generate_other_contour(
        self,
        position: Optional[np.ndarray] = None,
        noise_level: float = 0.02
    ) -> np.ndarray:
        """
        Generate random 'other' contour (background/noise).
        
        Random irregular shapes that don't match hand or tool patterns.
        """
        if position is None:
            position = self.rng.randn(2) * 0.05
        
        # Random Fourier series for irregular shape
        n_harmonics = self.rng.randint(3, 8)
        radii = self.rng.exponential(0.03, n_harmonics)
        phases = self.rng.uniform(0, 2 * np.pi, n_harmonics)
        
        contour = []
        for i in range(self.contour_points):
            angle = 2 * np.pi * i / self.contour_points
            r = 0.03  # Base radius
            for h in range(n_harmonics):
                r += radii[h] * np.cos((h + 1) * angle + phases[h])
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            contour.append([x, y])
        
        contour = np.array(contour)
        contour = contour + position
        contour += self.rng.randn(*contour.shape) * noise_level
        
        return contour.astype(np.float32)
    
    def generate_dataset(
        self,
        n_samples: int,
        class_distribution: Optional[Dict[str, float]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a complete labeled dataset.
        
        Parameters:
        -----------
        n_samples : int
            Total number of samples to generate
        class_distribution : dict
            Distribution of classes {'hand': 0.4, 'tool': 0.4, 'other': 0.2}
            
        Returns:
        --------
        X : np.ndarray, shape (n_samples, contour_points, 2)
            Contour data
        y : np.ndarray, shape (n_samples, num_classes)
            One-hot encoded labels
        """
        if class_distribution is None:
            class_distribution = {'hand': 0.4, 'tool': 0.4, 'other': 0.2}
        
        # Calculate samples per class
        class_counts = {}
        remaining = n_samples
        for cls, ratio in list(class_distribution.items())[:-1]:
            count = int(n_samples * ratio)
            class_counts[cls] = count
            remaining -= count
        class_counts[list(class_distribution.keys())[-1]] = remaining
        
        contours = []
        labels = []
        
        # Generate hand contours
        for _ in range(class_counts['hand']):
            contour = self.generate_hand_contour()
            contours.append(preprocess_contour(contour))
            labels.append([1, 0, 0])  # hand
        
        # Generate tool contours
        for _ in range(class_counts['tool']):
            contour = self.generate_tool_contour()
            contours.append(preprocess_contour(contour))
            labels.append([0, 1, 0])  # tool
        
        # Generate other contours
        for _ in range(class_counts['other']):
            contour = self.generate_other_contour()
            contours.append(preprocess_contour(contour))
            labels.append([0, 0, 1])  # other
        
        # Shuffle
        indices = self.rng.permutation(len(contours))
        X = np.array([contours[i] for i in indices])
        y = np.array([labels[i] for i in indices])
        
        return X, y


# =============================================================================
# TRAINING PIPELINE
# =============================================================================

def train_model(
    n_samples: int = 10000,
    epochs: int = ModelConfig.EPOCHS,
    batch_size: int = ModelConfig.BATCH_SIZE,
    validation_split: float = ModelConfig.VALIDATION_SPLIT,
    model_dir: str = 'models',
    verbose: int = 1
) -> Tuple[keras.Model, Dict]:
    """
    Train the intent classification model.
    
    Parameters:
    -----------
    n_samples : int
        Number of synthetic samples to generate
    epochs : int
        Number of training epochs
    batch_size : int
        Batch size for training
    validation_split : float
        Fraction of data for validation
    model_dir : str
        Directory to save model
    verbose : int
        Verbosity level
        
    Returns:
    --------
    model : keras.Model
        Trained model
    history : dict
        Training history
    """
    print("=" * 60)
    print("Shadow Intent Classifier - Training")
    print("=" * 60)
    
    # Generate synthetic data
    print(f"\n[1] Generating {n_samples} synthetic samples...")
    generator = SyntheticDataGenerator()
    X, y = generator.generate_dataset(n_samples)
    print(f"    Data shape: {X.shape}")
    print(f"    Labels shape: {y.shape}")
    
    # Split train/validation
    split_idx = int(len(X) * (1 - validation_split))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    print(f"    Training samples: {len(X_train)}")
    print(f"    Validation samples: {len(X_val)}")
    
    # Create model
    print("\n[2] Creating model...")
    model = create_intent_classifier()
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=10,
            restore_best_weights=True,
            verbose=verbose
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=verbose
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(model_dir, 'best_model.keras'),
            monitor='val_accuracy',
            save_best_only=True,
            verbose=verbose
        )
    ]
    
    # Train
    print(f"\n[3] Training for up to {epochs} epochs...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose
    )
    
    # Evaluate
    print("\n[4] Evaluating model...")
    train_loss, train_acc, _ = model.evaluate(X_train, y_train, verbose=0)
    val_loss, val_acc, _ = model.evaluate(X_val, y_val, verbose=0)
    
    print(f"    Training accuracy: {train_acc:.4f}")
    print(f"    Validation accuracy: {val_acc:.4f}")
    print(f"    Target accuracy: {ModelConfig.TARGET_ACCURACY}")
    print(f"    Target met: {'✓' if val_acc >= ModelConfig.TARGET_ACCURACY else '✗'}")
    
    # Model size
    size_mb = estimate_model_size_mb(model)
    print(f"\n[5] Model size: {size_mb:.3f} MB")
    
    # Save model and metadata
    print(f"\n[6] Saving model to {model_dir}...")
    os.makedirs(model_dir, exist_ok=True)
    
    # Save final model
    save_model(model, os.path.join(model_dir, 'intent_classifier.keras'))
    
    # Save metadata
    metadata = {
        'created_at': datetime.now().isoformat(),
        'n_samples': n_samples,
        'epochs_trained': len(history.history['loss']),
        'train_accuracy': float(train_acc),
        'val_accuracy': float(val_acc),
        'model_size_mb': float(size_mb),
        'target_accuracy': ModelConfig.TARGET_ACCURACY,
        'target_met': val_acc >= ModelConfig.TARGET_ACCURACY,
        'config': {
            'contour_points': ModelConfig.CONTOUR_POINTS,
            'num_classes': ModelConfig.NUM_CLASSES,
            'class_names': ModelConfig.CLASS_NAMES
        }
    }
    
    with open(os.path.join(model_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n[7] Training complete!")
    print(f"    Model saved: {model_dir}/intent_classifier.keras")
    print(f"    Metadata saved: {model_dir}/metadata.json")
    
    return model, history.history


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Train Shadow Intent Classifier')
    parser.add_argument('--samples', type=int, default=10000, help='Number of samples')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--model-dir', type=str, default='models', help='Model directory')
    parser.add_argument('--verbose', type=int, default=1, help='Verbosity')
    
    args = parser.parse_args()
    
    train_model(
        n_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        model_dir=args.model_dir,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
"""
Shadow Intelligence Layer - Intent Classification Model
======================================================

Lightweight CNN for classifying shadow intent from contour data.
Target: <1MB model, >92% accuracy, <5ms inference

Author: Cognitive AR Empire Technical Team
"""

import numpy as np
import tensorflow as tf
from typing import Tuple, List, Dict
from dataclasses import dataclass
import json


@dataclass
class ModelConfig:
    """Configuration for intent classification model."""
    input_points: int = 64  # Number of contour points
    input_dims: int = 3     # x, y, confidence
    num_classes: int = 3    # hand, tool, other
    conv1_filters: int = 32
    conv2_filters: int = 64
    dense_units: int = 64
    dropout_rate: float = 0.3
    learning_rate: float = 0.001


class IntentClassifier:
    """
    Lightweight CNN for shadow intent classification.
    
    Architecture:
    - Conv1D(32) -> ReLU -> MaxPool
    - Conv1D(64) -> ReLU -> MaxPool -> GlobalAvgPool
    - Dense(64) -> ReLU -> Dropout
    - Dense(3) -> Softmax
    
    Input: (batch, 64, 3) - contour points with confidence
    Output: (batch, 3) - probabilities for [hand, tool, other]
    """
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.model = self._build_model()
        self.class_names = ['hand', 'tool', 'other']
        
    def _build_model(self) -> tf.keras.Model:
        """Build the CNN model."""
        inputs = tf.keras.layers.Input(
            shape=(self.config.input_points, self.config.input_dims),
            name='contour_input'
        )
        
        # Conv block 1
        x = tf.keras.layers.Conv1D(
            self.config.conv1_filters, 3, padding='same', activation='relu',
            name='conv1'
        )(inputs)
        x = tf.keras.layers.BatchNormalization(name='bn1')(x)
        x = tf.keras.layers.MaxPooling1D(2, name='pool1')(x)
        
        # Conv block 2
        x = tf.keras.layers.Conv1D(
            self.config.conv2_filters, 3, padding='same', activation='relu',
            name='conv2'
        )(x)
        x = tf.keras.layers.BatchNormalization(name='bn2')(x)
        x = tf.keras.layers.MaxPooling1D(2, name='pool2')(x)
        
        # Global average pooling
        x = tf.keras.layers.GlobalAveragePooling1D(name='gap')(x)
        
        # Dense block
        x = tf.keras.layers.Dense(
            self.config.dense_units, activation='relu', name='dense1'
        )(x)
        x = tf.keras.layers.Dropout(self.config.dropout_rate, name='dropout')(x)
        
        # Output layer
        outputs = tf.keras.layers.Dense(
            self.config.num_classes, activation='softmax', name='output'
        )(x)
        
        model = tf.keras.Model(inputs, outputs, name='intent_classifier')
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(self.config.learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=2)]
        )
        
        return model
    
    def summary(self) -> str:
        """Get model summary as string."""
        string_list = []
        self.model.summary(print_fn=lambda x: string_list.append(x))
        return '\n'.join(string_list)
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return self.model.count_params()
    
    def get_model_size_kb(self) -> float:
        """Estimate model size in KB."""
        # Rough estimate: 4 bytes per float32 parameter
        return (self.count_parameters() * 4) / 1024
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        callbacks: List = None
    ) -> tf.keras.callbacks.History:
        """
        Train the model.
        
        Args:
            X_train: Training contours (N, 64, 3)
            y_train: Training labels one-hot (N, 3)
            X_val: Validation contours
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size
            callbacks: Optional Keras callbacks
            
        Returns:
            Training history
        """
        default_callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        all_callbacks = (callbacks or []) + default_callbacks
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=all_callbacks,
            verbose=1
        )
        
        return history
    
    def predict(self, contour: np.ndarray) -> Dict[str, any]:
        """
        Predict intent from contour.
        
        Args:
            contour: (64, 3) array of points with confidence
            
        Returns:
            Dictionary with class, confidence, and all probabilities
        """
        # Ensure correct shape
        if contour.ndim == 2:
            contour = np.expand_dims(contour, axis=0)
        
        # Predict
        predictions = self.model.predict(contour, verbose=0)
        probs = predictions[0]
        
        class_idx = np.argmax(probs)
        confidence = float(probs[class_idx])
        
        return {
            'class': self.class_names[class_idx],
            'class_index': int(class_idx),
            'confidence': confidence,
            'probabilities': {
                name: float(prob) for name, prob in zip(self.class_names, probs)
            }
        }
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test contours
            y_test: Test labels (one-hot)
            
        Returns:
            Dictionary with metrics
        """
        results = self.model.evaluate(X_test, y_test, verbose=0)
        
        # Get predictions for additional metrics
        predictions = self.model.predict(X_test, verbose=0)
        pred_classes = np.argmax(predictions, axis=1)
        true_classes = np.argmax(y_test, axis=1)
        
        # Per-class accuracy
        per_class_acc = {}
        for i, name in enumerate(self.class_names):
            mask = true_classes == i
            if mask.sum() > 0:
                per_class_acc[name] = float((pred_classes[mask] == i).mean())
        
        return {
            'loss': float(results[0]),
            'accuracy': float(results[1]),
            'top2_accuracy': float(results[2]),
            'per_class_accuracy': per_class_acc
        }
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        self.model.save(filepath)
        
        # Save config
        config_path = filepath.replace('.keras', '_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'input_points': self.config.input_points,
                'input_dims': self.config.input_dims,
                'num_classes': self.config.num_classes,
                'class_names': self.class_names
            }, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'IntentClassifier':
        """Load model from file."""
        # Load config
        config_path = filepath.replace('.keras', '_config.json')
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        
        config = ModelConfig(
            input_points=saved_config['input_points'],
            input_dims=saved_config['input_dims'],
            num_classes=saved_config['num_classes']
        )
        
        instance = cls(config)
        instance.model = tf.keras.models.load_model(filepath)
        instance.class_names = saved_config['class_names']
        
        return instance


def create_model_summary() -> str:
    """Create and summarize a fresh model."""
    classifier = IntentClassifier()
    
    summary = []
    summary.append("=" * 60)
    summary.append("INTENT CLASSIFIER MODEL SUMMARY")
    summary.append("=" * 60)
    summary.append(classifier.summary())
    summary.append("")
    summary.append(f"Trainable parameters: {classifier.count_parameters():,}")
    summary.append(f"Estimated size: {classifier.get_model_size_kb():.2f} KB")
    summary.append("=" * 60)
    
    return '\n'.join(summary)


if __name__ == "__main__":
    print(create_model_summary())
"""
Main entry point for Shadow Intelligence Layer.

Provides command-line interface for training, inference, and benchmarking.
"""

from __future__ import annotations

import os
import sys
import argparse
import numpy as np
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.intelligence_api import IntelligenceAPI, quick_classify
from inference.edge_inference import EdgeInferenceEngine, InferenceMode


def train_command(args):
    """Run training command."""
    from training.train_intent import TrainingPipeline, TrainingConfig
    
    config = TrainingConfig(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        export_tflite=True,
        quantize=args.quantize
    )
    
    pipeline = TrainingPipeline(config)
    pipeline.run_full_pipeline(regenerate_data=args.regenerate)


def infer_command(args):
    """Run inference command."""
    # Initialize API
    api = IntelligenceAPI(
        intent_model_path=args.intent_model,
        property_model_path=args.property_model,
        mode=args.mode
    )
    
    # Load or generate test data
    if args.input:
        import numpy as np
        data = np.load(args.input)
        shadow_data = data['shadow']
    else:
        # Generate dummy data
        shadow_data = np.random.rand(64, 64).astype(np.float32)
    
    # Run inference
    result = api.classify(shadow_data)
    
    # Print results
    print("\n" + "="*50)
    print("INFERENCE RESULT")
    print("="*50)
    print(f"\nObject Type: {result.object_type}")
    print(f"  Confidence: {result.object_confidence:.2%}")
    
    if result.is_hand():
        print(f"\nGrasp State: {result.grasp_state}")
        print(f"  Confidence: {result.grasp_confidence:.2%}")
        print(f"\nInteraction Intent: {result.interaction_intent}")
        print(f"  Confidence: {result.interaction_confidence:.2%}")
    
    print(f"\nMaterial: {result.material}")
    print(f"  Confidence: {result.material_confidence:.2%}")
    print(f"\nSize Category: {result.size_category}")
    print(f"  Confidence: {result.size_confidence:.2%}")
    
    print(f"\nOverall Confidence: {result.overall_confidence:.2%}")
    print(f"Inference Time: {result.inference_time_ms:.2f} ms")
    print("="*50)


def benchmark_command(args):
    """Run benchmark command."""
    from tests.benchmark_accuracy import run_accuracy_benchmark
    
    report = run_accuracy_benchmark(
        intent_model_path=args.intent_model,
        property_model_path=args.property_model,
        dataset_path=args.dataset,
        num_test_samples=args.samples
    )
    
    # Print summary
    report.print_summary()
    
    # Save report
    if args.output:
        import json
        with open(args.output, 'w') as f:
            f.write(report.to_json())
        print(f"\nReport saved to {args.output}")


def test_command(args):
    """Run test command."""
    import subprocess
    
    if args.test_type == "all":
        tests = ["tests/test_models.py", "tests/test_inference.py"]
    elif args.test_type == "models":
        tests = ["tests/test_models.py"]
    elif args.test_type == "inference":
        tests = ["tests/test_inference.py"]
    else:
        tests = [args.test_type]
    
    for test in tests:
        print(f"\nRunning {test}...")
        result = subprocess.run([sys.executable, test], capture_output=False)
        if result.returncode != 0:
            sys.exit(result.returncode)
    
    print("\n✅ All tests passed!")


def export_command(args):
    """Run export command."""
    from training.export_tflite import TFLiteExporter
    
    exporter = TFLiteExporter(args.model, args.type)
    
    # Load representative dataset if needed
    representative_dataset = None
    if args.optimization == "full_integer" and args.data:
        data = np.load(args.data)
        val_data = data['X_val'][:100]
        
        def rep_dataset():
            for i in range(len(val_data)):
                yield [val_data[i:i+1].astype(np.float32)]
        
        representative_dataset = rep_dataset
    
    # Export
    exporter.export(
        args.output,
        optimization=args.optimization,
        representative_dataset=representative_dataset
    )
    
    # Benchmark if requested
    if args.benchmark and args.data:
        data = np.load(args.data)
        test_data = data['X_val'][0]
        exporter.benchmark(args.output, test_data)


def demo_command(args):
    """Run demo command."""
    print("\n" + "="*70)
    print("SHADOW INTELLIGENCE LAYER - DEMO")
    print("="*70)
    
    # Initialize API
    api = IntelligenceAPI(
        intent_model_path=args.intent_model,
        property_model_path=args.property_model,
        mode=args.mode
    )
    
    print("\nProcessing 10 sample shadow observations...\n")
    
    for i in range(10):
        # Generate sample shadow data
        shadow_data = np.random.rand(64, 64).astype(np.float32)
        
        # Classify
        result = api.classify(shadow_data)
        
        # Print result
        print(f"Sample {i+1}:")
        print(f"  Object: {result.object_type:8} ({result.object_confidence:.1%})")
        if result.is_hand():
            print(f"  Grasp:  {result.grasp_state:8} ({result.grasp_confidence:.1%})")
        print(f"  Material: {result.material:6} | Size: {result.size_category}")
        print(f"  Latency: {result.inference_time_ms:.2f} ms")
        print()
    
    # Print performance stats
    stats = api.get_performance_stats()
    print("-"*50)
    print("Performance Statistics:")
    print(f"  Frames processed: {stats['inference_count']}")
    print(f"  Average latency: {stats['average_inference_time_ms']:.2f} ms")
    print(f"  Effective FPS: {1000/stats['average_inference_time_ms']:.1f}")
    print("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Shadow Intelligence Layer - TinyML for Intent Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train models
  python main.py train --samples 10000 --epochs 100

  # Run inference
  python main.py infer --input shadow.npy

  # Run benchmarks
  python main.py benchmark --samples 1000

  # Run tests
  python main.py test --type all

  # Export to TFLite
  python main.py export --model intent_model.keras --type intent

  # Run demo
  python main.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train models")
    train_parser.add_argument("--samples", type=int, default=10000, help="Number of samples")
    train_parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    train_parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    train_parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    train_parser.add_argument("--regenerate", action="store_true", help="Regenerate dataset")
    train_parser.add_argument("--no-quantize", action="store_true", help="Skip quantization")
    train_parser.set_defaults(quantize=True)
    
    # Infer command
    infer_parser = subparsers.add_parser("infer", help="Run inference")
    infer_parser.add_argument("--input", type=str, help="Input file (.npy)")
    infer_parser.add_argument("--intent-model", type=str, default="models/pretrained/intent_model.tflite")
    infer_parser.add_argument("--property-model", type=str, default="models/pretrained/property_model.tflite")
    infer_parser.add_argument("--mode", type=str, default="auto", choices=["cpu", "gpu", "npu", "auto"])
    
    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    bench_parser.add_argument("--intent-model", type=str, help="Intent model path")
    bench_parser.add_argument("--property-model", type=str, help="Property model path")
    bench_parser.add_argument("--dataset", type=str, help="Dataset path")
    bench_parser.add_argument("--samples", type=int, default=1000, help="Test samples")
    bench_parser.add_argument("--output", type=str, default="benchmark_report.json", help="Output file")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--type", type=str, default="all", 
                            choices=["all", "models", "inference"],
                            help="Test type")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export to TFLite")
    export_parser.add_argument("--model", type=str, required=True, help="Model path")
    export_parser.add_argument("--type", type=str, required=True, choices=["intent", "property"])
    export_parser.add_argument("--output", type=str, help="Output path")
    export_parser.add_argument("--optimization", type=str, default="default",
                               choices=["none", "default", "full_integer", "float16"])
    export_parser.add_argument("--data", type=str, help="Dataset for quantization")
    export_parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo")
    demo_parser.add_argument("--intent-model", type=str, default="models/pretrained/intent_model.tflite")
    demo_parser.add_argument("--property-model", type=str, default="models/pretrained/property_model.tflite")
    demo_parser.add_argument("--mode", type=str, default="auto", choices=["cpu", "gpu", "npu", "auto"])
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command
    commands = {
        "train": train_command,
        "infer": infer_command,
        "benchmark": benchmark_command,
        "test": test_command,
        "export": export_command,
        "demo": demo_command
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Shadow Intelligence Layer - Edge Inference
===========================================

Lightweight inference engine for intent classification on edge devices.
Supports both Keras and TFLite models.

Author: Cognitive AR Empire 2035 Technical Team
Version: 1.0
"""

import numpy as np
import time
from typing import Tuple, Optional, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
import os

# Try to import TensorFlow, but allow fallback to TFLite only
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Try to import TFLite runtime
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    try:
        from tensorflow import lite as tflite
        TFLITE_AVAILABLE = True
    except ImportError:
        TFLITE_AVAILABLE = False


# =============================================================================
# DATA TYPES
# =============================================================================

class IntentType(Enum):
    """Intent classification categories"""
    HAND = 0
    TOOL = 1
    OTHER = 2
    
    @classmethod
    def from_index(cls, idx: int) -> 'IntentType':
        """Get IntentType from index"""
        for intent in cls:
            if intent.value == idx:
                return intent
        return cls.OTHER


@dataclass
class IntentPrediction:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    probabilities: np.ndarray
    inference_time_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'intent': self.intent.name.lower(),
            'confidence': float(self.confidence),
            'probabilities': self.probabilities.tolist(),
            'inference_time_ms': float(self.inference_time_ms)
        }


# =============================================================================
# PREPROCESSING
# =============================================================================

CONTOUR_POINTS = 64
INPUT_DIM = 2


def preprocess_contour(
    contour: np.ndarray,
    target_points: int = CONTOUR_POINTS,
    normalize: bool = True
) -> np.ndarray:
    """
    Preprocess a contour for model input.
    
    Steps:
    1. Resample to fixed number of points
    2. Normalize coordinates to [-1, 1] range
    3. Ensure correct shape (points, 2)
    
    Parameters:
    -----------
    contour : np.ndarray
        Input contour, shape (N, 2) or (N*2,)
    target_points : int
        Number of points to resample to
    normalize : bool
        Whether to normalize coordinates
        
    Returns:
    --------
    processed : np.ndarray
        Processed contour, shape (target_points, 2)
    """
    # Ensure 2D array
    if contour.ndim == 1:
        contour = contour.reshape(-1, 2)
    
    # Resample to fixed number of points
    n_points = len(contour)
    if n_points != target_points:
        # Linear interpolation
        indices = np.linspace(0, n_points - 1, target_points)
        processed = np.zeros((target_points, 2))
        for i in range(2):
            processed[:, i] = np.interp(indices, np.arange(n_points), contour[:, i])
    else:
        processed = contour.copy()
    
    # Normalize to [-1, 1] range
    if normalize:
        # Center
        centroid = np.mean(processed, axis=0)
        processed = processed - centroid
        
        # Scale to unit bounding box
        max_range = np.max(np.abs(processed))
        if max_range > 0:
            processed = processed / max_range
    
    return processed.astype(np.float32)


def batch_preprocess(contours: List[np.ndarray]) -> np.ndarray:
    """Preprocess a batch of contours"""
    processed = [preprocess_contour(c) for c in contours]
    return np.array(processed)


# =============================================================================
# INFERENCE ENGINE
# =============================================================================

class IntentClassifier:
    """
    Edge inference engine for intent classification.
    Supports Keras (.keras) and TFLite (.tflite) models.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_tflite: bool = False
    ):
        """
        Initialize the classifier.
        
        Parameters:
        -----------
        model_path : str, optional
            Path to model file (.keras or .tflite)
        use_tflite : bool
            Force use of TFLite runtime
        """
        self.model_path = model_path
        self.use_tflite = use_tflite or (model_path and model_path.endswith('.tflite'))
        self.model = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.class_names = ['hand', 'tool', 'other']
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> None:
        """
        Load a model from file.
        
        Parameters:
        -----------
        model_path : str
            Path to model file
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model_path = model_path
        self.use_tflite = model_path.endswith('.tflite')
        
        if self.use_tflite:
            self._load_tflite_model(model_path)
        else:
            self._load_keras_model(model_path)
        
        print(f"Model loaded: {model_path}")
    
    def _load_keras_model(self, model_path: str) -> None:
        """Load Keras model"""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow not available. Use TFLite model instead.")
        
        self.model = keras.models.load_model(model_path)
        self.interpreter = None
    
    def _load_tflite_model(self, model_path: str) -> None:
        """Load TFLite model"""
        if TFLITE_AVAILABLE:
            self.interpreter = tflite.Interpreter(model_path=model_path)
        elif TF_AVAILABLE:
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
        else:
            raise RuntimeError("TFLite runtime not available")
        
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.model = None
    
    def predict(
        self,
        contour: np.ndarray,
        return_dict: bool = False
    ) -> Union[IntentPrediction, Dict]:
        """
        Predict intent from a single contour.
        
        Parameters:
        -----------
        contour : np.ndarray
            Input contour, shape (N, 2) or (N*2,)
        return_dict : bool
            Return result as dictionary instead of dataclass
            
        Returns:
        --------
        prediction : IntentPrediction or dict
            Classification result
        """
        # Preprocess
        processed = preprocess_contour(contour)
        processed = np.expand_dims(processed, axis=0)  # Add batch dimension
        
        # Run inference
        start_time = time.perf_counter()
        
        if self.use_tflite and self.interpreter:
            # TFLite inference
            self.interpreter.set_tensor(self.input_details[0]['index'], processed)
            self.interpreter.invoke()
            probabilities = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        elif self.model:
            # Keras inference
            probabilities = self.model.predict(processed, verbose=0)[0]
        else:
            raise RuntimeError("No model loaded")
        
        inference_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Get prediction
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]
        
        result = IntentPrediction(
            intent=IntentType.from_index(predicted_class),
            confidence=float(confidence),
            probabilities=probabilities,
            inference_time_ms=inference_time
        )
        
        return result.to_dict() if return_dict else result
    
    def predict_batch(
        self,
        contours: List[np.ndarray]
    ) -> List[IntentPrediction]:
        """
        Predict intents for a batch of contours.
        
        Parameters:
        -----------
        contours : List[np.ndarray]
            List of input contours
            
        Returns:
        --------
        predictions : List[IntentPrediction]
            List of classification results
        """
        # Preprocess batch
        processed = batch_preprocess(contours)
        
        # Run inference
        start_time = time.perf_counter()
        
        if self.use_tflite and self.interpreter:
            # TFLite batch inference (may need to loop)
            all_probs = []
            for i in range(len(processed)):
                self.interpreter.set_tensor(
                    self.input_details[0]['index'],
                    np.expand_dims(processed[i], axis=0)
                )
                self.interpreter.invoke()
                probs = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                all_probs.append(probs)
            probabilities = np.array(all_probs)
        elif self.model:
            # Keras batch inference
            probabilities = self.model.predict(processed, verbose=0)
        else:
            raise RuntimeError("No model loaded")
        
        total_time = (time.perf_counter() - start_time) * 1000  # ms
        per_item_time = total_time / len(contours)
        
        # Create results
        results = []
        for i, probs in enumerate(probabilities):
            predicted_class = np.argmax(probs)
            confidence = probs[predicted_class]
            results.append(IntentPrediction(
                intent=IntentType.from_index(predicted_class),
                confidence=float(confidence),
                probabilities=probs,
                inference_time_ms=per_item_time
            ))
        
        return results
    
    def benchmark(
        self,
        n_iterations: int = 100,
        warmup: int = 10
    ) -> Dict:
        """
        Benchmark inference latency.
        
        Parameters:
        -----------
        n_iterations : int
            Number of iterations to benchmark
        warmup : int
            Number of warmup iterations
            
        Returns:
        --------
        results : dict
            Benchmark statistics
        """
        # Generate random test input
        test_contour = np.random.randn(CONTOUR_POINTS, INPUT_DIM).astype(np.float32)
        
        # Warmup
        for _ in range(warmup):
            self.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            self.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        times = np.array(times)
        
        return {
            'mean_ms': float(np.mean(times)),
            'std_ms': float(np.std(times)),
            'min_ms': float(np.min(times)),
            'max_ms': float(np.max(times)),
            'p50_ms': float(np.percentile(times, 50)),
            'p95_ms': float(np.percentile(times, 95)),
            'p99_ms': float(np.percentile(times, 99)),
            'n_iterations': n_iterations
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_classifier(model_path: str) -> IntentClassifier:
    """Load a classifier from model file"""
    return IntentClassifier(model_path)


def predict_intent(
    contour: np.ndarray,
    model_path: str = 'models/intent_classifier.keras'
) -> Dict:
    """
    One-shot intent prediction.
    
    Parameters:
    -----------
    contour : np.ndarray
        Input contour
    model_path : str
        Path to model file
        
    Returns:
    --------
    result : dict
        Prediction result with intent, confidence, probabilities, inference_time_ms
    """
    classifier = IntentClassifier(model_path)
    return classifier.predict(contour, return_dict=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Demo inference"""
    print("=" * 60)
    print("Shadow Intent Classifier - Inference Demo")
    print("=" * 60)
    
    # Generate test contours
    from train import SyntheticDataGenerator
    
    generator = SyntheticDataGenerator()
    
    # Test with each class
    test_cases = [
        ('hand', generator.generate_hand_contour()),
        ('tool', generator.generate_tool_contour()),
        ('other', generator.generate_other_contour())
    ]
    
    # Check for available model
    model_path = 'models/intent_classifier.keras'
    tflite_path = 'models/intent_classifier_int8.tflite'
    
    if os.path.exists(tflite_path):
        print(f"\nUsing TFLite model: {tflite_path}")
        classifier = IntentClassifier(tflite_path)
    elif os.path.exists(model_path):
        print(f"\nUsing Keras model: {model_path}")
        classifier = IntentClassifier(model_path)
    else:
        print(f"\nNo trained model found. Run train.py first.")
        return
    
    # Run predictions
    print("\nPredictions:")
    print("-" * 60)
    
    for true_class, contour in test_cases:
        result = classifier.predict(contour)
        print(f"\nTrue class: {true_class}")
        print(f"  Predicted: {result.intent.name.lower()} (confidence: {result.confidence:.3f})")
        print(f"  Probabilities: hand={result.probabilities[0]:.3f}, "
              f"tool={result.probabilities[1]:.3f}, other={result.probabilities[2]:.3f}")
        print(f"  Inference time: {result.inference_time_ms:.3f} ms")
    
    # Benchmark
    print("\n" + "=" * 60)
    print("Benchmarking inference latency...")
    print("=" * 60)
    
    benchmark_results = classifier.benchmark(n_iterations=100)
    
    print(f"\nLatency Statistics (100 iterations):")
    print(f"  Mean: {benchmark_results['mean_ms']:.3f} ms")
    print(f"  Std:  {benchmark_results['std_ms']:.3f} ms")
    print(f"  Min:  {benchmark_results['min_ms']:.3f} ms")
    print(f"  Max:  {benchmark_results['max_ms']:.3f} ms")
    print(f"  P95:  {benchmark_results['p95_ms']:.3f} ms")
    print(f"  P99:  {benchmark_results['p99_ms']:.3f} ms")
    
    target_ms = 5.0
    print(f"\nTarget latency: {target_ms} ms")
    print(f"Target met: {'✓' if benchmark_results['p95_ms'] < target_ms else '✗'}")


if __name__ == "__main__":
    main()
"""
Shadow Intelligence Layer - TFLite Export
==========================================

Export Keras models to TensorFlow Lite format with quantization.
Supports float32, float16, and int8 quantization.

Author: Cognitive AR Empire 2035 Technical Team
Version: 1.0
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
import os
from typing import Optional, Tuple, Dict
import argparse

from model import ModelConfig, create_intent_classifier, preprocess_contour
from train import SyntheticDataGenerator


# =============================================================================
# TFLITE EXPORTER
# =============================================================================

class TFLiteExporter:
    """Export Keras models to optimized TFLite format"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize exporter.
        
        Parameters:
        -----------
        model_path : str, optional
            Path to Keras model file
        """
        self.model = None
        self.model_path = model_path
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> None:
        """Load Keras model from file"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model = keras.models.load_model(model_path)
        self.model_path = model_path
        print(f"Loaded model: {model_path}")
    
    def export_float32(
        self,
        output_path: str,
        optimize: bool = True
    ) -> str:
        """
        Export model as float32 TFLite.
        
        Parameters:
        -----------
        output_path : str
            Output file path
        optimize : bool
            Apply default optimizations
            
        Returns:
        --------
        output_path : str
            Path to exported model
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if optimize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        size_kb = len(tflite_model) / 1024
        print(f"Exported float32 model: {output_path} ({size_kb:.2f} KB)")
        
        return output_path
    
    def export_float16(
        self,
        output_path: str
    ) -> str:
        """
        Export model as float16 quantized TFLite.
        Reduces model size by ~50% with minimal accuracy loss.
        
        Parameters:
        -----------
        output_path : str
            Output file path
            
        Returns:
        --------
        output_path : str
            Path to exported model
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        
        tflite_model = converter.convert()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        size_kb = len(tflite_model) / 1024
        print(f"Exported float16 model: {output_path} ({size_kb:.2f} KB)")
        
        return output_path
    
    def export_int8(
        self,
        output_path: str,
        representative_dataset: Optional[tf.data.Dataset] = None,
        num_calibration_samples: int = 500
    ) -> str:
        """
        Export model as int8 quantized TFLite.
        Reduces model size by ~75% for edge deployment.
        
        Parameters:
        -----------
        output_path : str
            Output file path
        representative_dataset : tf.data.Dataset, optional
            Dataset for calibration
        num_calibration_samples : int
            Number of samples to generate if no dataset provided
            
        Returns:
        --------
        output_path : str
            Path to exported model
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Int8 quantization requires representative dataset
        if representative_dataset is None:
            representative_dataset = self._generate_representative_data(num_calibration_samples)
        
        def representative_data_gen():
            for input_value in representative_dataset.batch(1).take(num_calibration_samples):
                yield [input_value[0].numpy()]
        
        converter.representative_dataset = representative_data_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        size_kb = len(tflite_model) / 1024
        print(f"Exported int8 model: {output_path} ({size_kb:.2f} KB)")
        
        return output_path
    
    def _generate_representative_data(
        self,
        n_samples: int
    ) -> tf.data.Dataset:
        """Generate representative dataset for quantization calibration"""
        generator = SyntheticDataGenerator()
        
        # Generate samples from all classes
        X, _ = generator.generate_dataset(n_samples)
        
        dataset = tf.data.Dataset.from_tensor_slices(X)
        return dataset
    
    def export_all(
        self,
        output_dir: str = 'models',
        base_name: str = 'intent_classifier'
    ) -> Dict[str, str]:
        """
        Export model in all formats.
        
        Parameters:
        -----------
        output_dir : str
            Output directory
        base_name : str
            Base filename
            
        Returns:
        --------
        paths : dict
            Dictionary of format -> path
        """
        os.makedirs(output_dir, exist_ok=True)
        
        paths = {}
        
        # Float32
        paths['float32'] = self.export_float32(
            os.path.join(output_dir, f'{base_name}_float32.tflite')
        )
        
        # Float16
        paths['float16'] = self.export_float16(
            os.path.join(output_dir, f'{base_name}_float16.tflite')
        )
        
        # Int8
        paths['int8'] = self.export_int8(
            os.path.join(output_dir, f'{base_name}_int8.tflite')
        )
        
        return paths


# =============================================================================
# MODEL VERIFICATION
# =============================================================================

def verify_tflite_model(
    tflite_path: str,
    keras_path: Optional[str] = None,
    n_test_samples: int = 100
) -> Dict:
    """
    Verify TFLite model accuracy against Keras model.
    
    Parameters:
    -----------
    tflite_path : str
        Path to TFLite model
    keras_path : str, optional
        Path to Keras model for comparison
    n_test_samples : int
        Number of test samples
        
    Returns:
    --------
    results : dict
        Verification results
    """
    print(f"\nVerifying TFLite model: {tflite_path}")
    
    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Generate test data
    generator = SyntheticDataGenerator()
    X_test, y_test = generator.generate_dataset(n_test_samples)
    
    # Run TFLite inference
    tflite_predictions = []
    for i in range(len(X_test)):
        input_data = np.expand_dims(X_test[i], axis=0).astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])[0]
        tflite_predictions.append(output)
    
    tflite_predictions = np.array(tflite_predictions)
    tflite_classes = np.argmax(tflite_predictions, axis=1)
    true_classes = np.argmax(y_test, axis=1)
    
    tflite_accuracy = np.mean(tflite_classes == true_classes)
    
    results = {
        'tflite_accuracy': float(tflite_accuracy),
        'n_test_samples': n_test_samples
    }
    
    # Compare with Keras if provided
    if keras_path and os.path.exists(keras_path):
        keras_model = keras.models.load_model(keras_path)
        keras_predictions = keras_model.predict(X_test, verbose=0)
        keras_classes = np.argmax(keras_predictions, axis=1)
        keras_accuracy = np.mean(keras_classes == true_classes)
        
        # Agreement between models
        agreement = np.mean(tflite_classes == keras_classes)
        
        results['keras_accuracy'] = float(keras_accuracy)
        results['model_agreement'] = float(agreement)
        
        print(f"  Keras accuracy: {keras_accuracy:.4f}")
        print(f"  TFLite accuracy: {tflite_accuracy:.4f}")
        print(f"  Model agreement: {agreement:.4f}")
    else:
        print(f"  TFLite accuracy: {tflite_accuracy:.4f}")
    
    return results


def compare_model_sizes(model_dir: str = 'models') -> Dict[str, float]:
    """
    Compare sizes of all model formats.
    
    Parameters:
    -----------
    model_dir : str
        Directory containing models
        
    Returns:
    --------
    sizes : dict
        Model name -> size in KB
    """
    sizes = {}
    
    for filename in os.listdir(model_dir):
        filepath = os.path.join(model_dir, filename)
        if os.path.isfile(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            sizes[filename] = size_kb
    
    print("\nModel Size Comparison:")
    print("-" * 50)
    for name, size in sorted(sizes.items(), key=lambda x: x[1]):
        print(f"  {name:40s} {size:8.2f} KB")
    
    return sizes


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Export model to TFLite')
    parser.add_argument('--model', type=str, default='models/intent_classifier.keras',
                        help='Path to Keras model')
    parser.add_argument('--output-dir', type=str, default='models',
                        help='Output directory')
    parser.add_argument('--formats', type=str, default='all',
                        choices=['all', 'float32', 'float16', 'int8'],
                        help='Export formats')
    parser.add_argument('--verify', action='store_true',
                        help='Verify exported models')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Shadow Intent Classifier - TFLite Export")
    print("=" * 60)
    
    # Check if model exists
    if not os.path.exists(args.model):
        print(f"\nModel not found: {args.model}")
        print("Please train a model first using: python train.py")
        return
    
    # Create exporter
    exporter = TFLiteExporter(args.model)
    
    # Export
    print(f"\nExporting model from: {args.model}")
    print(f"Output directory: {args.output_dir}")
    
    if args.formats == 'all':
        paths = exporter.export_all(args.output_dir)
    elif args.formats == 'float32':
        paths = {'float32': exporter.export_float32(
            os.path.join(args.output_dir, 'intent_classifier_float32.tflite')
        )}
    elif args.formats == 'float16':
        paths = {'float16': exporter.export_float16(
            os.path.join(args.output_dir, 'intent_classifier_float16.tflite')
        )}
    elif args.formats == 'int8':
        paths = {'int8': exporter.export_int8(
            os.path.join(args.output_dir, 'intent_classifier_int8.tflite')
        )}
    
    # Compare sizes
    sizes = compare_model_sizes(args.output_dir)
    
    # Verify if requested
    if args.verify:
        for format_name, path in paths.items():
            verify_tflite_model(path, args.model)
    
    print("\n" + "=" * 60)
    print("Export complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
"""
Training package for Shadow Intelligence Layer.
"""

from training.generate_dataset import (
    DatasetGenerator,
    ShadowGenerator,
    generate_synthetic_dataset
)

__all__ = [
    'DatasetGenerator',
    'ShadowGenerator',
    'generate_synthetic_dataset'
]
"""
Export Intent Classifier to TensorFlow Lite
===========================================

Converts trained Keras model to optimized TFLite format.
Supports quantization for edge deployment.

Usage:
    python training/export_tflite.py --input models/pretrained/intent_model.keras
"""

import tensorflow as tf
import numpy as np
import argparse
import os
from pathlib import Path


def representative_dataset_generator(n_samples: int = 100):
    """Generate representative data for quantization calibration."""
    for _ in range(n_samples):
        # Generate random contour similar to training data
        data = np.random.randn(1, 64, 3).astype(np.float32)
        # Normalize like training
        data[:, :, :2] -= data[:, :, :2].mean()
        data[:, :, :2] /= (data[:, :, :2].std() + 1e-7)
        yield [data]


def convert_to_tflite(
    keras_model_path: str,
    output_path: str = None,
    quantize: bool = True,
    optimize: bool = True
) -> str:
    """
    Convert Keras model to TensorFlow Lite.
    
    Args:
        keras_model_path: Path to .keras model file
        output_path: Output path (default: same name with .tflite)
        quantize: Apply int8 quantization
        optimize: Apply optimizations
        
    Returns:
        Path to saved TFLite model
    """
    if output_path is None:
        output_path = keras_model_path.replace('.keras', '.tflite')
    
    print(f"Converting: {keras_model_path}")
    print(f"Output: {output_path}")
    
    # Load Keras model
    model = tf.keras.models.load_model(keras_model_path)
    
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Apply optimizations
    if optimize:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        print("  ✓ Default optimizations enabled")
    
    if quantize:
        # Full integer quantization for smallest size
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS_INT8
        ]
        converter.representative_dataset = representative_dataset_generator
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        print("  ✓ INT8 quantization enabled")
    
    # Convert
    print("\nConverting model...")
    tflite_model = converter.convert()
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    # Get file sizes
    keras_size = os.path.getsize(keras_model_path) / 1024
    tflite_size = os.path.getsize(output_path) / 1024
    
    print(f"\nConversion complete!")
    print(f"  Keras size: {keras_size:.2f} KB")
    print(f"  TFLite size: {tflite_size:.2f} KB")
    print(f"  Compression: {keras_size/tflite_size:.2f}x")
    
    # Verify model
    print("\nVerifying TFLite model...")
    verify_tflite_model(output_path)
    
    return output_path


def verify_tflite_model(model_path: str) -> bool:
    """
    Verify TFLite model can be loaded and run.
    
    Args:
        model_path: Path to TFLite model
        
    Returns:
        True if verification passed
    """
    try:
        # Load interpreter
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        
        # Get input/output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"  Input shape: {input_details[0]['shape']}")
        print(f"  Input dtype: {input_details[0]['dtype']}")
        print(f"  Output shape: {output_details[0]['shape']}")
        print(f"  Output dtype: {output_details[0]['dtype']}")
        
        # Test inference
        test_input = np.random.randn(1, 64, 3).astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], test_input)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        
        print(f"  Test output shape: {output.shape}")
        print(f"  Test output sum: {output.sum():.4f} (should be ~1.0)")
        
        if abs(output.sum() - 1.0) < 0.1:
            print("  ✓ Verification passed")
            return True
        else:
            print("  ✗ Verification failed - output doesn't sum to 1")
            return False
            
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False


def compare_models(
    keras_path: str,
    tflite_path: str,
    n_tests: int = 100
) -> dict:
    """
    Compare Keras and TFLite model outputs.
    
    Args:
        keras_path: Path to Keras model
        tflite_path: Path to TFLite model
        n_tests: Number of test samples
        
    Returns:
        Comparison metrics
    """
    print("\nComparing model outputs...")
    
    # Load models
    keras_model = tf.keras.models.load_model(keras_path)
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Generate test data
    differences = []
    
    for _ in range(n_tests):
        test_input = np.random.randn(1, 64, 3).astype(np.float32)
        test_input[:, :, :2] -= test_input[:, :, :2].mean()
        test_input[:, :, :2] /= (test_input[:, :, :2].std() + 1e-7)
        
        # Keras prediction
        keras_pred = keras_model.predict(test_input, verbose=0)
        
        # TFLite prediction (may need dequantization)
        interpreter.set_tensor(input_details[0]['index'], test_input)
        interpreter.invoke()
        tflite_pred = interpreter.get_tensor(output_details[0]['index'])
        
        # Calculate difference
        diff = np.abs(keras_pred - tflite_pred).mean()
        differences.append(diff)
    
    differences = np.array(differences)
    
    results = {
        'mean_difference': float(np.mean(differences)),
        'max_difference': float(np.max(differences)),
        'n_tests': n_tests
    }
    
    print(f"  Mean difference: {results['mean_difference']:.6f}")
    print(f"  Max difference: {results['max_difference']:.6f}")
    
    if results['mean_difference'] < 0.1:
        print("  ✓ Models are equivalent")
    else:
        print("  ⚠️  Models differ significantly")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Export to TFLite')
    parser.add_argument('--input', type=str, 
                        default='models/pretrained/intent_model.keras',
                        help='Input Keras model path')
    parser.add_argument('--output', type=str, default=None,
                        help='Output TFLite path')
    parser.add_argument('--no-quantize', action='store_true',
                        help='Disable quantization')
    parser.add_argument('--no-optimize', action='store_true',
                        help='Disable optimizations')
    parser.add_argument('--compare', action='store_true',
                        help='Compare with original model')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TENSORFLOW LITE EXPORT")
    print("=" * 60)
    
    # Check input exists
    if not os.path.exists(args.input):
        print(f"Error: Input model not found: {args.input}")
        print("Run training/train.py first to create a model")
        return
    
    # Convert
    tflite_path = convert_to_tflite(
        args.input,
        args.output,
        quantize=not args.no_quantize,
        optimize=not args.no_optimize
    )
    
    # Compare if requested
    if args.compare:
        compare_models(args.input, tflite_path)
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"\nModel saved to: {tflite_path}")
    print(f"Size: {os.path.getsize(tflite_path) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
"""
Synthetic Dataset Generation for Shadow Intelligence Layer.

Generates training data for intent classification and property prediction
using shadow simulation. Creates realistic shadow patterns for:
- Human hands in various poses
- Tools (screwdrivers, hammers, etc.)
- Generic objects

Includes data augmentation for robustness.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
import json


class ObjectType(Enum):
    """Object type categories."""
    HAND = 0
    TOOL = 1
    OTHER = 2


class GraspState(Enum):
    """Hand grasp states."""
    OPEN = 0
    CLOSED = 1
    PINCHING = 2


class InteractionIntent(Enum):
    """Interaction intent categories."""
    POINTING = 0
    MANIPULATING = 1
    RESTING = 2


class MaterialType(Enum):
    """Material type categories."""
    RIGID = 0
    SOFT = 1
    LIQUID = 2


class SizeCategory(Enum):
    """Size categories."""
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


@dataclass
class ShadowSample:
    """Single synthetic shadow sample with labels."""
    shadow: np.ndarray
    object_type: ObjectType
    grasp_state: GraspState
    interaction_intent: InteractionIntent
    material: MaterialType
    size_category: SizeCategory
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'shadow': self.shadow,
            'object_type': self.object_type.value,
            'grasp_state': self.grasp_state.value,
            'interaction_intent': self.interaction_intent.value,
            'material': self.material.value,
            'size_category': self.size_category.value
        }


class ShadowGenerator:
    """Generates synthetic shadow data for training."""
    
    def __init__(
        self,
        image_size: Tuple[int, int] = (64, 64),
        noise_level: float = 0.05,
        seed: Optional[int] = None
    ) -> None:
        """
        Initialize shadow generator.
        
        Args:
            image_size: Output image dimensions (H, W)
            noise_level: Amount of noise to add (0-1)
            seed: Random seed for reproducibility
        """
        self.image_size = image_size
        self.noise_level = noise_level
        
        if seed is not None:
            np.random.seed(seed)
    
    def generate_hand_shadow(
        self,
        grasp_state: GraspState,
        interaction_intent: InteractionIntent,
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic hand shadow.
        
        Args:
            grasp_state: Hand grasp configuration
            interaction_intent: Type of interaction
            size_category: Size of the hand
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        # Scale based on size category
        scale = {SizeCategory.SMALL: 0.6, SizeCategory.MEDIUM: 0.8, SizeCategory.LARGE: 1.0}[size_category]
        
        # Palm center position
        palm_x = w // 2
        palm_y = h // 2 + int(5 * scale)
        
        # Draw palm (ellipse)
        palm_width = int(25 * scale)
        palm_height = int(20 * scale)
        self._draw_ellipse(shadow, palm_x, palm_y, palm_width, palm_height, 1.0)
        
        # Draw fingers based on grasp state
        if grasp_state == GraspState.OPEN:
            # Extended fingers
            finger_angles = [-30, -10, 10, 30]  # Degrees
            finger_lengths = [int(35 * scale), int(38 * scale), int(36 * scale), int(30 * scale)]
            
            for angle, length in zip(finger_angles, finger_lengths):
                self._draw_finger(shadow, palm_x, palm_y - palm_height//2, angle, length, scale)
        
        elif grasp_state == GraspState.CLOSED:
            # Curled fingers
            finger_angles = [-25, -8, 8, 25]
            for angle in finger_angles:
                self._draw_curled_finger(shadow, palm_x, palm_y - palm_height//2, angle, scale)
        
        elif grasp_state == GraspState.PINCHING:
            # Index and thumb extended, others curled
            self._draw_finger(shadow, palm_x - 5, palm_y - palm_height//2, -15, int(35 * scale), scale)
            self._draw_finger(shadow, palm_x + 5, palm_y - palm_height//2, 20, int(30 * scale), scale)
            # Other fingers curled
            for angle in [-25, 25]:
                self._draw_curled_finger(shadow, palm_x, palm_y - palm_height//2, angle, scale)
        
        # Add interaction intent modifications
        if interaction_intent == InteractionIntent.POINTING:
            # Emphasize one finger (index)
            self._draw_finger(shadow, palm_x - 5, palm_y - palm_height//2, -15, int(45 * scale), scale * 1.2)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def generate_tool_shadow(
        self,
        tool_type: str = "screwdriver",
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic tool shadow.
        
        Args:
            tool_type: Type of tool (screwdriver, hammer, wrench, etc.)
            size_category: Size of the tool
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        scale = {SizeCategory.SMALL: 0.5, SizeCategory.MEDIUM: 0.75, SizeCategory.LARGE: 1.0}[size_category]
        
        center_x = w // 2
        center_y = h // 2
        
        if tool_type == "screwdriver":
            # Handle
            handle_width = int(8 * scale)
            handle_length = int(25 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + handle_length//2,
                handle_width, handle_length, 1.0
            )
            # Shaft
            shaft_width = int(3 * scale)
            shaft_length = int(30 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y - shaft_length//2 - 5,
                shaft_width, shaft_length, 0.9
            )
        
        elif tool_type == "hammer":
            # Handle
            handle_width = int(10 * scale)
            handle_length = int(35 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + 10,
                handle_width, handle_length, 1.0
            )
            # Head
            head_width = int(30 * scale)
            head_height = int(12 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y - 15,
                head_width, head_height, 1.0
            )
        
        elif tool_type == "wrench":
            # Handle
            handle_width = int(8 * scale)
            handle_length = int(30 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + 5,
                handle_width, handle_length, 1.0
            )
            # Head (C-shape)
            head_size = int(15 * scale)
            self._draw_circle(shadow, center_x, center_y - 15, head_size, 1.0)
            # Cutout
            self._draw_circle(shadow, center_x, center_y - 15, head_size//2, 0.0)
        
        else:  # Generic tool
            length = int(40 * scale)
            width = int(12 * scale)
            self._draw_rectangle(shadow, center_x, center_y, width, length, 1.0)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def generate_object_shadow(
        self,
        object_shape: str = "box",
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic generic object shadow.
        
        Args:
            object_shape: Shape type (box, sphere, cylinder)
            size_category: Size of the object
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        scale = {SizeCategory.SMALL: 0.4, SizeCategory.MEDIUM: 0.7, SizeCategory.LARGE: 1.0}[size_category]
        
        center_x = w // 2
        center_y = h // 2
        
        if object_shape == "box":
            width = int(30 * scale)
            height = int(25 * scale)
            self._draw_rectangle(shadow, center_x, center_y, width, height, 1.0)
        
        elif object_shape == "sphere":
            radius = int(18 * scale)
            self._draw_circle(shadow, center_x, center_y, radius, 1.0)
        
        elif object_shape == "cylinder":
            width = int(20 * scale)
            height = int(35 * scale)
            self._draw_ellipse(shadow, center_x, center_y, width, height, 1.0)
        
        else:  # Irregular shape
            # Generate random polygon
            num_points = np.random.randint(5, 9)
            radius = int(20 * scale)
            points = []
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points + np.random.uniform(-0.3, 0.3)
                r = radius * np.random.uniform(0.7, 1.3)
                px = int(center_x + r * np.cos(angle))
                py = int(center_y + r * np.sin(angle))
                points.append((px, py))
            self._draw_polygon(shadow, points, 1.0)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def _draw_ellipse(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        width: int, height: int,
        intensity: float
    ) -> None:
        """Draw filled ellipse on image."""
        h, w = img.shape
        y, x = np.ogrid[:h, :w]
        mask = ((x - cx) ** 2 / (width/2) ** 2 + (y - cy) ** 2 / (height/2) ** 2) <= 1
        img[mask] = intensity
    
    def _draw_circle(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        radius: int,
        intensity: float
    ) -> None:
        """Draw filled circle on image."""
        h, w = img.shape
        y, x = np.ogrid[:h, :w]
        mask = ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2
        img[mask] = intensity
    
    def _draw_rectangle(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        width: int, height: int,
        intensity: float
    ) -> None:
        """Draw filled rectangle on image."""
        h, w = img.shape
        x1 = max(0, cx - width // 2)
        x2 = min(w, cx + width // 2)
        y1 = max(0, cy - height // 2)
        y2 = min(h, cy + height // 2)
        img[y1:y2, x1:x2] = intensity
    
    def _draw_finger(
        self,
        img: np.ndarray,
        start_x: int, start_y: int,
        angle_deg: float,
        length: int,
        width: float
    ) -> None:
        """Draw a finger extending from a point."""
        angle_rad = np.deg2rad(angle_deg - 90)  # Adjust for image coordinates
        
        finger_width = max(3, int(6 * width))
        
        for i in range(length):
            x = int(start_x + i * np.cos(angle_rad))
            y = int(start_y + i * np.sin(angle_rad))
            self._draw_circle(img, x, y, finger_width // 2, 1.0)
    
    def _draw_curled_finger(
        self,
        img: np.ndarray,
        start_x: int, start_y: int,
        angle_deg: float,
        scale: float
    ) -> None:
        """Draw a curled finger."""
        angle_rad = np.deg2rad(angle_deg - 90)
        length = int(15 * scale)
        
        # First segment (extending)
        for i in range(length):
            x = int(start_x + i * np.cos(angle_rad))
            y = int(start_y + i * np.sin(angle_rad))
            self._draw_circle(img, x, y, max(2, int(5 * scale)), 1.0)
        
        # Second segment (curled back)
        mid_x = int(start_x + length * np.cos(angle_rad))
        mid_y = int(start_y + length * np.sin(angle_rad))
        curl_angle = angle_rad + np.deg2rad(90)
        
        for i in range(int(length * 0.7)):
            x = int(mid_x + i * np.cos(curl_angle))
            y = int(mid_y + i * np.sin(curl_angle))
            self._draw_circle(img, x, y, max(2, int(4 * scale)), 1.0)
    
    def _draw_polygon(
        self,
        img: np.ndarray,
        points: List[Tuple[int, int]],
        intensity: float
    ) -> None:
        """Draw filled polygon on image."""
        from skimage.draw import polygon as sk_polygon
        
        if len(points) < 3:
            return
        
        rows = [p[1] for p in points]
        cols = [p[0] for p in points]
        
        try:
            rr, cc = sk_polygon(rows, cols, shape=img.shape)
            img[rr, cc] = intensity
        except ImportError:
            # Fallback: draw as connected circles
            for i, (x, y) in enumerate(points):
                self._draw_circle(img, x, y, 5, intensity)
                if i > 0:
                    prev_x, prev_y = points[i-1]
                    # Draw line
                    num_steps = max(abs(x - prev_x), abs(y - prev_y))
                    for t in range(num_steps):
                        px = int(prev_x + t * (x - prev_x) / num_steps)
                        py = int(prev_y + t * (y - prev_y) / num_steps)
                        self._draw_circle(img, px, py, 3, intensity)
    
    def _add_noise(self, img: np.ndarray) -> np.ndarray:
        """Add realistic noise to shadow."""
        noise = np.random.normal(0, self.noise_level, img.shape)
        img_noisy = img + noise
        
        # Add slight blur for realism
        from scipy.ndimage import gaussian_filter
        img_noisy = gaussian_filter(img_noisy, sigma=0.5)
        
        # Clip to valid range
        return np.clip(img_noisy, 0, 1).astype(np.float32)


class DatasetGenerator:
    """Generates complete training datasets."""
    
    def __init__(
        self,
        image_size: Tuple[int, int] = (64, 64),
        num_samples: int = 10000,
        train_split: float = 0.8,
        seed: int = 42
    ) -> None:
        """
        Initialize dataset generator.
        
        Args:
            image_size: Size of generated images
            num_samples: Total number of samples to generate
            train_split: Fraction for training set
            seed: Random seed
        """
        self.image_size = image_size
        self.num_samples = num_samples
        self.train_split = train_split
        self.seed = seed
        
        self.shadow_gen = ShadowGenerator(image_size, seed=seed)
    
    def generate_dataset(
        self,
        augment: bool = True,
        augmentation_factor: float = 0.3
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Generate complete dataset with train/val split.
        
        Args:
            augment: Whether to apply data augmentation
            augmentation_factor: Probability of applying each augmentation
        
        Returns:
            Dictionary with 'train' and 'val' keys, each containing:
                - 'X': Input images (N, H, W, 1)
                - 'y_object': Object type labels (N, 3)
                - 'y_grasp': Grasp state labels (N, 3)
                - 'y_interaction': Interaction intent labels (N, 3)
                - 'y_material': Material labels (N, 3)
                - 'y_size': Size category labels (N, 3)
        """
        np.random.seed(self.seed)
        
        samples = []
        
        # Generate samples for each category
        samples_per_type = self.num_samples // 3
        
        # Generate hand samples
        for _ in range(samples_per_type):
            grasp = np.random.choice(list(GraspState))
            intent = np.random.choice(list(InteractionIntent))
            size = np.random.choice(list(SizeCategory))
            
            shadow = self.shadow_gen.generate_hand_shadow(grasp, intent, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.HAND,
                grasp_state=grasp,
                interaction_intent=intent,
                material=MaterialType.SOFT,  # Hands are soft
                size_category=size
            ))
        
        # Generate tool samples
        tool_types = ["screwdriver", "hammer", "wrench", "generic"]
        for _ in range(samples_per_type):
            tool = np.random.choice(tool_types)
            size = np.random.choice(list(SizeCategory))
            
            shadow = self.shadow_gen.generate_tool_shadow(tool, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.TOOL,
                grasp_state=GraspState.OPEN,  # N/A for tools
                interaction_intent=InteractionIntent.RESTING,  # N/A for tools
                material=MaterialType.RIGID,  # Tools are rigid
                size_category=size
            ))
        
        # Generate other object samples
        shapes = ["box", "sphere", "cylinder", "irregular"]
        for _ in range(samples_per_type):
            shape = np.random.choice(shapes)
            size = np.random.choice(list(SizeCategory))
            material = np.random.choice(list(MaterialType))
            
            shadow = self.shadow_gen.generate_object_shadow(shape, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.OTHER,
                grasp_state=GraspState.OPEN,
                interaction_intent=InteractionIntent.RESTING,
                material=material,
                size_category=size
            ))
        
        # Shuffle samples
        np.random.shuffle(samples)
        
        # Apply augmentation if requested
        if augment:
            samples = self._augment_samples(samples, augmentation_factor)
        
        # Split into train/val
        split_idx = int(len(samples) * self.train_split)
        train_samples = samples[:split_idx]
        val_samples = samples[split_idx:]
        
        # Convert to arrays
        train_data = self._samples_to_arrays(train_samples)
        val_data = self._samples_to_arrays(val_samples)
        
        return {
            'train': train_data,
            'val': val_data
        }
    
    def _augment_samples(
        self,
        samples: List[ShadowSample],
        factor: float
    ) -> List[ShadowSample]:
        """Apply data augmentation to samples."""
        augmented = []
        
        for sample in samples:
            augmented.append(sample)
            
            # Random rotation
            if np.random.random() < factor:
                from scipy.ndimage import rotate
                angle = np.random.uniform(-30, 30)
                rotated = rotate(sample.shadow, angle, reshape=False, mode='constant')
                augmented.append(ShadowSample(
                    shadow=rotated,
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
            
            # Random scaling
            if np.random.random() < factor:
                from scipy.ndimage import zoom
                scale = np.random.uniform(0.8, 1.2)
                scaled = zoom(sample.shadow, scale, mode='constant')
                # Crop or pad to original size
                h, w = self.image_size
                sh, sw = scaled.shape
                if sh > h or sw > w:
                    start_y = (sh - h) // 2
                    start_x = (sw - w) // 2
                    scaled = scaled[start_y:start_y+h, start_x:start_x+w]
                else:
                    padded = np.zeros((h, w))
                    start_y = (h - sh) // 2
                    start_x = (w - sw) // 2
                    padded[start_y:start_y+sh, start_x:start_x+sw] = scaled
                    scaled = padded
                augmented.append(ShadowSample(
                    shadow=scaled.astype(np.float32),
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
            
            # Random translation
            if np.random.random() < factor:
                from scipy.ndimage import shift
                tx = np.random.randint(-5, 6)
                ty = np.random.randint(-5, 6)
                translated = shift(sample.shadow, (ty, tx), mode='constant')
                augmented.append(ShadowSample(
                    shadow=translated,
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
        
        return augmented
    
    def _samples_to_arrays(
        self,
        samples: List[ShadowSample]
    ) -> Dict[str, np.ndarray]:
        """Convert samples to numpy arrays."""
        n = len(samples)
        h, w = self.image_size
        
        X = np.zeros((n, h, w, 1), dtype=np.float32)
        y_object = np.zeros((n, 3), dtype=np.float32)
        y_grasp = np.zeros((n, 3), dtype=np.float32)
        y_interaction = np.zeros((n, 3), dtype=np.float32)
        y_material = np.zeros((n, 3), dtype=np.float32)
        y_size = np.zeros((n, 3), dtype=np.float32)
        
        for i, sample in enumerate(samples):
            X[i, :, :, 0] = sample.shadow
            y_object[i, sample.object_type.value] = 1.0
            y_grasp[i, sample.grasp_state.value] = 1.0
            y_interaction[i, sample.interaction_intent.value] = 1.0
            y_material[i, sample.material.value] = 1.0
            y_size[i, sample.size_category.value] = 1.0
        
        return {
            'X': X,
            'y_object': y_object,
            'y_grasp': y_grasp,
            'y_interaction': y_interaction,
            'y_material': y_material,
            'y_size': y_size
        }
    
    def save_dataset(
        self,
        dataset: Dict[str, Dict[str, np.ndarray]],
        path: str
    ) -> None:
        """Save dataset to disk."""
        np.savez_compressed(
            path,
            X_train=dataset['train']['X'],
            y_object_train=dataset['train']['y_object'],
            y_grasp_train=dataset['train']['y_grasp'],
            y_interaction_train=dataset['train']['y_interaction'],
            y_material_train=dataset['train']['y_material'],
            y_size_train=dataset['train']['y_size'],
            X_val=dataset['val']['X'],
            y_object_val=dataset['val']['y_object'],
            y_grasp_val=dataset['val']['y_grasp'],
            y_interaction_val=dataset['val']['y_interaction'],
            y_material_val=dataset['val']['y_material'],
            y_size_val=dataset['val']['y_size']
        )
        print(f"Dataset saved to {path}")
    
    @staticmethod
    def load_dataset(path: str) -> Dict[str, Dict[str, np.ndarray]]:
        """Load dataset from disk."""
        data = np.load(path)
        
        return {
            'train': {
                'X': data['X_train'],
                'y_object': data['y_object_train'],
                'y_grasp': data['y_grasp_train'],
                'y_interaction': data['y_interaction_train'],
                'y_material': data['y_material_train'],
                'y_size': data['y_size_train']
            },
            'val': {
                'X': data['X_val'],
                'y_object': data['y_object_val'],
                'y_grasp': data['y_grasp_val'],
                'y_interaction': data['y_interaction_val'],
                'y_material': data['y_material_val'],
                'y_size': data['y_size_val']
            }
        }


def generate_synthetic_dataset(
    output_path: str,
    num_samples: int = 10000,
    image_size: Tuple[int, int] = (64, 64),
    seed: int = 42
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Generate and save a synthetic dataset.
    
    Args:
        output_path: Path to save dataset
        num_samples: Number of samples to generate
        image_size: Size of generated images
        seed: Random seed
    
    Returns:
        Generated dataset dictionary
    """
    generator = DatasetGenerator(
        image_size=image_size,
        num_samples=num_samples,
        seed=seed
    )
    
    dataset = generator.generate_dataset(augment=True)
    generator.save_dataset(dataset, output_path)
    
    return dataset


if __name__ == "__main__":
    # Generate example dataset
    dataset = generate_synthetic_dataset(
        output_path="shadow_dataset.npz",
        num_samples=10000,
        image_size=(64, 64),
        seed=42
    )
    
    print(f"Training samples: {len(dataset['train']['X'])}")
    print(f"Validation samples: {len(dataset['val']['X'])}")
"""
Training Script for Intent Classifier
=====================================

Generates synthetic data and trains the intent classification model.

Usage:
    python training/train.py --epochs 50 --samples 10000
"""

import numpy as np
import tensorflow as tf
import argparse
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from model import IntentClassifier, ModelConfig


def generate_synthetic_contour(
    contour_type: str,
    n_points: int = 64,
    noise_level: float = 0.01
) -> np.ndarray:
    """
    Generate synthetic contour for a given type.
    
    Args:
        contour_type: 'hand', 'tool', or 'other'
        n_points: Number of contour points
        noise_level: Amount of random noise
        
    Returns:
        (n_points, 3) array of (x, y, confidence)
    """
    t = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    
    if contour_type == 'hand':
        # Hand-like shape: palm + fingers approximation
        # Use superellipse-like shape with finger protrusions
        a, b = 0.045, 0.06  # Palm dimensions
        
        # Base palm shape
        x = a * np.sign(np.cos(t)) * np.abs(np.cos(t))**0.7
        y = b * np.sign(np.sin(t)) * np.abs(np.sin(t))**0.5
        
        # Add finger protrusions (5 fingers)
        for i in range(5):
            finger_angle = i * 2 * np.pi / 5
            finger_width = 0.3
            finger_length = 0.04
            
            # Gaussian bump for each finger
            angle_diff = np.abs(np.mod(t - finger_angle + np.pi, 2*np.pi) - np.pi)
            finger_mask = angle_diff < finger_width
            
            x[finger_mask] += finger_length * np.cos(finger_angle) * \
                              np.exp(-angle_diff[finger_mask]**2 / (2 * 0.1**2))
            y[finger_mask] += finger_length * np.sin(finger_angle) * \
                              np.exp(-angle_diff[finger_mask]**2 / (2 * 0.1**2))
    
    elif contour_type == 'tool':
        # Tool-like shape: elongated rectangle or cylinder
        length, width = 0.12, 0.02
        
        # Rectangle with rounded corners
        x = length * np.cos(t)
        y = width * np.sin(t)
        
        # Add handle
        handle_mask = np.abs(t - np.pi) < 0.5
        x[handle_mask] *= 0.6
        y[handle_mask] *= 1.5
    
    else:  # 'other'
        # Random irregular shape
        n_harmonics = np.random.randint(3, 8)
        radius = 0.03
        
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        
        for h in range(1, n_harmonics + 1):
            amp = np.random.uniform(0.005, 0.02) / h
            phase = np.random.uniform(0, 2 * np.pi)
            radius_h = radius + amp * np.sin(h * t + phase)
        
        x = radius_h * np.cos(t)
        y = radius_h * np.sin(t)
    
    # Add noise
    x += np.random.normal(0, noise_level, n_points)
    y += np.random.normal(0, noise_level, n_points)
    
    # Confidence based on distance from center (higher for clearer edges)
    distances = np.sqrt(x**2 + y**2)
    confidence = 0.7 + 0.3 * (distances / distances.max())
    confidence += np.random.normal(0, 0.05, n_points)
    confidence = np.clip(confidence, 0, 1)
    
    return np.column_stack([x, y, confidence])


def generate_dataset(
    n_samples: int,
    n_points: int = 64
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training dataset.
    
    Args:
        n_samples: Total number of samples
        n_points: Points per contour
        
    Returns:
        X: (n_samples, n_points, 3) contours
        y: (n_samples, 3) one-hot labels
    """
    class_names = ['hand', 'tool', 'other']
    n_per_class = n_samples // 3
    
    X_list = []
    y_list = []
    
    for class_idx, class_name in enumerate(class_names):
        for _ in range(n_per_class):
            contour = generate_synthetic_contour(class_name, n_points)
            X_list.append(contour)
            
            label = np.zeros(3)
            label[class_idx] = 1
            y_list.append(label)
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    return X, y


def normalize_contours(X: np.ndarray) -> np.ndarray:
    """
    Normalize contours to standard scale.
    
    Args:
        X: (N, 64, 3) contours
        
    Returns:
        Normalized contours
    """
    X_norm = X.copy()
    
    for i in range(len(X_norm)):
        # Center
        centroid = X_norm[i, :, :2].mean(axis=0)
        X_norm[i, :, :2] -= centroid
        
        # Scale to unit variance
        scale = X_norm[i, :, :2].std()
        if scale > 0:
            X_norm[i, :, :2] /= scale
    
    return X_norm


def train_model(
    n_samples: int = 10000,
    epochs: int = 50,
    batch_size: int = 32,
    output_dir: str = "models/pretrained"
) -> Dict:
    """
    Train intent classifier model.
    
    Args:
        n_samples: Number of synthetic samples
        epochs: Training epochs
        batch_size: Batch size
        output_dir: Where to save model
        
    Returns:
        Training results dictionary
    """
    print("=" * 60)
    print("TRAINING INTENT CLASSIFIER")
    print("=" * 60)
    
    # Generate data
    print(f"\n[1] Generating {n_samples} synthetic samples...")
    X, y = generate_dataset(n_samples)
    X = normalize_contours(X)
    print(f"    Dataset shape: X={X.shape}, y={y.shape}")
    
    # Split
    print("\n[2] Splitting dataset...")
    split_idx = int(0.8 * len(X))
    val_split_idx = int(0.9 * len(X))
    
    X_train, y_train = X[:split_idx], y[:split_idx]
    X_val, y_val = X[split_idx:val_split_idx], y[split_idx:val_split_idx]
    X_test, y_test = X[val_split_idx:], y[val_split_idx:]
    
    print(f"    Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Create model
    print("\n[3] Creating model...")
    config = ModelConfig()
    classifier = IntentClassifier(config)
    print(f"    Parameters: {classifier.count_parameters():,}")
    print(f"    Est. size: {classifier.get_model_size_kb():.2f} KB")
    
    # Train
    print(f"\n[4] Training for up to {epochs} epochs...")
    history = classifier.train(
        X_train, y_train,
        X_val, y_val,
        epochs=epochs,
        batch_size=batch_size
    )
    
    # Evaluate
    print("\n[5] Evaluating on test set...")
    metrics = classifier.evaluate(X_test, y_test)
    
    print(f"    Test accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"    Test loss: {metrics['loss']:.4f}")
    print("    Per-class accuracy:")
    for name, acc in metrics['per_class_accuracy'].items():
        print(f"      {name}: {acc*100:.2f}%")
    
    # Save
    print(f"\n[6] Saving model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, 'intent_model.keras')
    classifier.save(model_path)
    print(f"    Saved: {model_path}")
    
    # Save metrics
    metrics_path = os.path.join(output_dir, 'training_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"    Saved: {metrics_path}")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    
    return {
        'model_path': model_path,
        'metrics': metrics,
        'history': history.history
    }


def main():
    parser = argparse.ArgumentParser(description='Train intent classifier')
    parser.add_argument('--samples', type=int, default=10000,
                        help='Number of synthetic samples')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Batch size')
    parser.add_argument('--output', type=str, default='models/pretrained',
                        help='Output directory')
    
    args = parser.parse_args()
    
    results = train_model(
        n_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        output_dir=args.output
    )
    
    # Check if accuracy target met
    accuracy = results['metrics']['accuracy']
    if accuracy >= 0.92:
        print(f"\n✅ TARGET MET: Accuracy {accuracy*100:.1f}% >= 92%")
    else:
        print(f"\n⚠️  TARGET NOT MET: Accuracy {accuracy*100:.1f}% < 92%")
        print("   Consider increasing samples or epochs")


if __name__ == "__main__":
    main()
"""
Training Pipeline for Shadow Intelligence Layer.

Trains both intent classifier and property predictor models
using synthetic data with proper validation and checkpointing.
"""

from __future__ import annotations

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.intent_classifier import IntentClassifier, ModelConfig
from models.property_predictor import PropertyPredictor, PropertyModelConfig
from training.generate_dataset import DatasetGenerator


@dataclass
class TrainingConfig:
    """Configuration for training pipeline."""
    # Data
    num_samples: int = 10000
    image_size: Tuple[int, int] = (64, 64)
    train_split: float = 0.8
    
    # Training
    batch_size: int = 32
    epochs: int = 100
    learning_rate: float = 0.001
    early_stopping_patience: int = 15
    reduce_lr_patience: int = 7
    
    # Model
    dropout_rate: float = 0.3
    use_separable_conv: bool = True
    
    # Paths
    data_dir: str = "data"
    model_dir: str = "models/pretrained"
    log_dir: str = "logs"
    
    # Export
    export_tflite: bool = True
    quantize: bool = True


class TrainingPipeline:
    """Complete training pipeline for intelligence models."""
    
    def __init__(self, config: TrainingConfig) -> None:
        """Initialize training pipeline."""
        self.config = config
        self._setup_directories()
        
        # Set random seeds for reproducibility
        np.random.seed(42)
        tf.random.set_seed(42)
    
    def _setup_directories(self) -> None:
        """Create necessary directories."""
        for dir_path in [self.config.data_dir, self.config.model_dir, self.config.log_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def generate_or_load_data(
        self,
        regenerate: bool = False
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """Generate or load training data."""
        dataset_path = os.path.join(self.config.data_dir, "shadow_dataset.npz")
        
        if os.path.exists(dataset_path) and not regenerate:
            print(f"Loading existing dataset from {dataset_path}")
            from training.generate_dataset import DatasetGenerator
            return DatasetGenerator.load_dataset(dataset_path)
        
        print("Generating new synthetic dataset...")
        generator = DatasetGenerator(
            image_size=self.config.image_size,
            num_samples=self.config.num_samples,
            train_split=self.config.train_split,
            seed=42
        )
        
        dataset = generator.generate_dataset(augment=True)
        generator.save_dataset(dataset, dataset_path)
        
        return dataset
    
    def train_intent_classifier(
        self,
        dataset: Dict[str, Dict[str, np.ndarray]]
    ) -> Tuple[IntentClassifier, Dict[str, Any]]:
        """
        Train intent classification model.
        
        Returns:
            Trained model and training history
        """
        print("\n" + "="*60)
        print("Training Intent Classifier")
        print("="*60)
        
        # Create model
        model_config = ModelConfig(
            input_shape=(*self.config.image_size, 1),
            dropout_rate=self.config.dropout_rate,
            use_separable_conv=self.config.use_separable_conv
        )
        
        model = IntentClassifier(model_config)
        model.summary()
        
        print(f"\nModel parameters: {model.count_parameters():,}")
        
        # Compile
        optimizer = keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        model.compile(optimizer=optimizer)
        
        # Prepare labels
        y_train = {
            "object_type": dataset['train']['y_object'],
            "grasp_state": dataset['train']['y_grasp'],
            "interaction_intent": dataset['train']['y_interaction']
        }
        
        y_val = {
            "object_type": dataset['val']['y_object'],
            "grasp_state": dataset['val']['y_grasp'],
            "interaction_intent": dataset['val']['y_interaction']
        }
        
        # Callbacks
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=self.config.reduce_lr_patience,
                min_lr=1e-7,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                os.path.join(self.config.model_dir, f"intent_best_{timestamp}.keras"),
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.TensorBoard(
                log_dir=os.path.join(self.config.log_dir, f"intent_{timestamp}"),
                histogram_freq=1
            )
        ]
        
        # Train
        print(f"\nTraining on {len(dataset['train']['X'])} samples...")
        print(f"Validating on {len(dataset['val']['X'])} samples...")
        
        history = model.fit(
            dataset['train']['X'],
            y_train,
            validation_data=(dataset['val']['X'], y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print("\n" + "-"*60)
        print("Final Evaluation")
        print("-"*60)
        results = model.evaluate(dataset['val']['X'], y_val)
        
        for metric, value in results.items():
            print(f"{metric}: {value:.4f}")
        
        # Calculate overall accuracy
        object_acc = results.get('object_type_accuracy', 0)
        grasp_acc = results.get('grasp_state_accuracy', 0)
        interaction_acc = results.get('interaction_intent_accuracy', 0)
        overall_acc = (object_acc + grasp_acc + interaction_acc) / 3
        
        print(f"\nOverall Intent Classification Accuracy: {overall_acc*100:.2f}%")
        
        # Save final model
        final_path = os.path.join(self.config.model_dir, "intent_model.keras")
        model.save(final_path)
        print(f"\nModel saved to {final_path}")
        
        # Export TFLite
        if self.config.export_tflite:
            tflite_path = os.path.join(self.config.model_dir, "intent_model.tflite")
            
            # Create representative dataset for quantization
            def representative_dataset():
                for i in range(min(100, len(dataset['val']['X']))):
                    yield [dataset['val']['X'][i:i+1].astype(np.float32)]
            
            model.export_tflite(
                tflite_path,
                optimize=self.config.quantize,
                representative_dataset=representative_dataset if self.config.quantize else None
            )
        
        return model, history.history
    
    def train_property_predictor(
        self,
        dataset: Dict[str, Dict[str, np.ndarray]]
    ) -> Tuple[PropertyPredictor, Dict[str, Any]]:
        """
        Train property prediction model.
        
        Returns:
            Trained model and training history
        """
        print("\n" + "="*60)
        print("Training Property Predictor")
        print("="*60)
        
        # Create model
        model_config = PropertyModelConfig(
            input_shape=(*self.config.image_size, 1),
            dropout_rate=self.config.dropout_rate,
            use_separable_conv=self.config.use_separable_conv
        )
        
        model = PropertyPredictor(model_config)
        model.summary()
        
        print(f"\nModel parameters: {model.count_parameters():,}")
        
        # Compile
        optimizer = keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        model.compile(optimizer=optimizer)
        
        # Prepare labels
        y_train = {
            "material": dataset['train']['y_material'],
            "size_category": dataset['train']['y_size']
        }
        
        y_val = {
            "material": dataset['val']['y_material'],
            "size_category": dataset['val']['y_size']
        }
        
        # Callbacks
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=self.config.early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=self.config.reduce_lr_patience,
                min_lr=1e-7,
                verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                os.path.join(self.config.model_dir, f"property_best_{timestamp}.keras"),
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.TensorBoard(
                log_dir=os.path.join(self.config.log_dir, f"property_{timestamp}"),
                histogram_freq=1
            )
        ]
        
        # Train
        print(f"\nTraining on {len(dataset['train']['X'])} samples...")
        print(f"Validating on {len(dataset['val']['X'])} samples...")
        
        history = model.fit(
            dataset['train']['X'],
            y_train,
            validation_data=(dataset['val']['X'], y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Evaluate
        print("\n" + "-"*60)
        print("Final Evaluation")
        print("-"*60)
        results = model.evaluate(dataset['val']['X'], y_val)
        
        for metric, value in results.items():
            print(f"{metric}: {value:.4f}")
        
        # Calculate overall accuracy
        material_acc = results.get('material_accuracy', 0)
        size_acc = results.get('size_category_accuracy', 0)
        overall_acc = (material_acc + size_acc) / 2
        
        print(f"\nOverall Property Prediction Accuracy: {overall_acc*100:.2f}%")
        
        # Save final model
        final_path = os.path.join(self.config.model_dir, "property_model.keras")
        model.save(final_path)
        print(f"\nModel saved to {final_path}")
        
        # Export TFLite
        if self.config.export_tflite:
            tflite_path = os.path.join(self.config.model_dir, "property_model.tflite")
            
            # Create representative dataset for quantization
            def representative_dataset():
                for i in range(min(100, len(dataset['val']['X']))):
                    yield [dataset['val']['X'][i:i+1].astype(np.float32)]
            
            model.export_tflite(
                tflite_path,
                optimize=self.config.quantize,
                representative_dataset=representative_dataset if self.config.quantize else None
            )
        
        return model, history.history
    
    def run_full_pipeline(
        self,
        regenerate_data: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete training pipeline.
        
        Returns:
            Dictionary with training results and metrics
        """
        print("\n" + "="*70)
        print("SHADOW INTELLIGENCE LAYER - TRAINING PIPELINE")
        print("="*70)
        print(f"\nConfiguration:")
        print(f"  Samples: {self.config.num_samples}")
        print(f"  Image size: {self.config.image_size}")
        print(f"  Batch size: {self.config.batch_size}")
        print(f"  Max epochs: {self.config.epochs}")
        print(f"  Learning rate: {self.config.learning_rate}")
        
        # Generate/load data
        dataset = self.generate_or_load_data(regenerate=regenerate_data)
        
        # Train intent classifier
        intent_model, intent_history = self.train_intent_classifier(dataset)
        
        # Train property predictor
        property_model, property_history = self.train_property_predictor(dataset)
        
        # Compile results
        results = {
            'intent_model': {
                'parameters': intent_model.count_parameters(),
                'model_size_mb': intent_model.get_model_size(),
                'history': intent_history
            },
            'property_model': {
                'parameters': property_model.count_parameters(),
                'model_size_mb': property_model.get_model_size(),
                'history': property_history
            }
        }
        
        # Save results
        results_path = os.path.join(self.config.log_dir, "training_results.json")
        with open(results_path, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json.dump(results, f, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
        
        print("\n" + "="*70)
        print("TRAINING PIPELINE COMPLETE")
        print("="*70)
        print(f"\nResults saved to {results_path}")
        
        return results


def main():
    """Main entry point for training."""
    parser = argparse.ArgumentParser(description="Train Shadow Intelligence Models")
    parser.add_argument("--samples", type=int, default=10000, help="Number of training samples")
    parser.add_argument("--epochs", type=int, default=100, help="Maximum training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate dataset")
    parser.add_argument("--no-tflite", action="store_true", help="Skip TFLite export")
    parser.add_argument("--no-quantize", action="store_true", help="Skip quantization")
    
    args = parser.parse_args()
    
    config = TrainingConfig(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        export_tflite=not args.no_tflite,
        quantize=not args.no_quantize
    )
    
    pipeline = TrainingPipeline(config)
    pipeline.run_full_pipeline(regenerate_data=args.regenerate)


if __name__ == "__main__":
    main()
"""
Accuracy Benchmarks for Shadow Intelligence Layer.

Comprehensive accuracy testing with detailed metrics and reporting.
"""

from __future__ import annotations

import os
import sys
import numpy as np
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.intent_classifier import IntentClassifier, create_intent_classifier
from models.property_predictor import PropertyPredictor, create_property_predictor
from training.generate_dataset import DatasetGenerator
from inference.edge_inference import EdgeInferenceEngine, InferenceMode


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for a classification task."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    per_class_accuracy: Dict[str, float]
    confusion_matrix: np.ndarray
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['confusion_matrix'] = self.confusion_matrix.tolist()
        return result


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    intent_metrics: Dict[str, AccuracyMetrics]
    property_metrics: Dict[str, AccuracyMetrics]
    overall_intent_accuracy: float
    overall_property_accuracy: float
    model_sizes_mb: Dict[str, float]
    inference_times_ms: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'intent_metrics': {
                k: v.to_dict() for k, v in self.intent_metrics.items()
            },
            'property_metrics': {
                k: v.to_dict() for k, v in self.property_metrics.items()
            },
            'overall_intent_accuracy': self.overall_intent_accuracy,
            'overall_property_accuracy': self.overall_property_accuracy,
            'model_sizes_mb': self.model_sizes_mb,
            'inference_times_ms': self.inference_times_ms
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def print_summary(self) -> None:
        """Print formatted summary."""
        print("\n" + "="*70)
        print("ACCURACY BENCHMARK REPORT")
        print("="*70)
        
        print("\n📊 INTENT CLASSIFICATION")
        print("-"*40)
        print(f"Overall Accuracy: {self.overall_intent_accuracy*100:.2f}%")
        print(f"Target: >92% {'✅ PASS' if self.overall_intent_accuracy > 0.92 else '❌ FAIL'}")
        
        for task, metrics in self.intent_metrics.items():
            print(f"\n  {task.upper()}:")
            print(f"    Accuracy:  {metrics.accuracy*100:.2f}%")
            print(f"    Precision: {metrics.precision*100:.2f}%")
            print(f"    Recall:    {metrics.recall*100:.2f}%")
            print(f"    F1 Score:  {metrics.f1_score*100:.2f}%")
        
        print("\n📊 PROPERTY PREDICTION")
        print("-"*40)
        print(f"Overall Accuracy: {self.overall_property_accuracy*100:.2f}%")
        print(f"Target: >90% {'✅ PASS' if self.overall_property_accuracy > 0.90 else '❌ FAIL'}")
        
        for task, metrics in self.property_metrics.items():
            print(f"\n  {task.upper()}:")
            print(f"    Accuracy:  {metrics.accuracy*100:.2f}%")
            print(f"    Precision: {metrics.precision*100:.2f}%")
            print(f"    Recall:    {metrics.recall*100:.2f}%")
            print(f"    F1 Score:  {metrics.f1_score*100:.2f}%")
        
        print("\n📦 MODEL SIZES")
        print("-"*40)
        for model, size in self.model_sizes_mb.items():
            print(f"  {model}: {size:.2f} MB")
            print(f"    Target: <5MB {'✅ PASS' if size < 5.0 else '❌ FAIL'}")
        
        print("\n⚡ INFERENCE TIMES")
        print("-"*40)
        for model, time_ms in self.inference_times_ms.items():
            print(f"  {model}: {time_ms:.2f} ms")
            print(f"    Target: <5ms {'✅ PASS' if time_ms < 5.0 else '⚠️  CPU (expected <5ms on NPU)'}")


class AccuracyBenchmark:
    """Benchmark accuracy of intelligence models."""
    
    def __init__(
        self,
        intent_model: IntentClassifier,
        property_model: PropertyPredictor,
        test_data: Dict[str, np.ndarray]
    ) -> None:
        """
        Initialize benchmark.
        
        Args:
            intent_model: Trained intent classifier
            property_model: Trained property predictor
            test_data: Test dataset dictionary
        """
        self.intent_model = intent_model
        self.property_model = property_model
        self.test_data = test_data
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_names: List[str]
    ) -> AccuracyMetrics:
        """
        Calculate comprehensive accuracy metrics.
        
        Args:
            y_true: True labels (one-hot encoded)
            y_pred: Predicted labels (one-hot encoded)
            class_names: List of class names
        
        Returns:
            AccuracyMetrics object
        """
        # Convert to class indices
        true_classes = np.argmax(y_true, axis=1)
        pred_classes = np.argmax(y_pred, axis=1)
        
        num_classes = len(class_names)
        
        # Accuracy
        accuracy = np.mean(true_classes == pred_classes)
        
        # Confusion matrix
        confusion = np.zeros((num_classes, num_classes), dtype=int)
        for t, p in zip(true_classes, pred_classes):
            confusion[t, p] += 1
        
        # Per-class metrics
        per_class_accuracy = {}
        precisions = []
        recalls = []
        
        for i, name in enumerate(class_names):
            # True positives
            tp = confusion[i, i]
            # False positives
            fp = np.sum(confusion[:, i]) - tp
            # False negatives
            fn = np.sum(confusion[i, :]) - tp
            
            # Per-class accuracy
            class_total = np.sum(confusion[i, :])
            per_class_accuracy[name] = tp / class_total if class_total > 0 else 0.0
            
            # Precision and recall
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            precisions.append(precision)
            recalls.append(recall)
        
        # Macro-averaged metrics
        macro_precision = np.mean(precisions)
        macro_recall = np.mean(recalls)
        macro_f1 = 2 * (macro_precision * macro_recall) / (macro_precision + macro_recall) \
            if (macro_precision + macro_recall) > 0 else 0.0
        
        return AccuracyMetrics(
            accuracy=accuracy,
            precision=macro_precision,
            recall=macro_recall,
            f1_score=macro_f1,
            per_class_accuracy=per_class_accuracy,
            confusion_matrix=confusion
        )
    
    def benchmark_intent(self) -> Dict[str, AccuracyMetrics]:
        """Benchmark intent classification accuracy."""
        print("\nBenchmarking intent classification...")
        
        # Get predictions
        X = self.test_data['X']
        
        predictions = self.intent_model.predict(X)
        
        # Extract predictions into arrays
        n = len(X)
        y_object_pred = np.zeros((n, 3))
        y_grasp_pred = np.zeros((n, 3))
        y_interaction_pred = np.zeros((n, 3))
        
        for i, pred in enumerate(predictions):
            obj_idx = ["hand", "tool", "other"].index(pred.object_type)
            grasp_idx = ["open", "closed", "pinching"].index(pred.grasp_state)
            interaction_idx = ["pointing", "manipulating", "resting"].index(pred.interaction_intent)
            
            y_object_pred[i, obj_idx] = 1.0
            y_grasp_pred[i, grasp_idx] = 1.0
            y_interaction_pred[i, interaction_idx] = 1.0
        
        # Calculate metrics
        metrics = {}
        
        metrics['object_type'] = self.calculate_metrics(
            self.test_data['y_object'],
            y_object_pred,
            ["hand", "tool", "other"]
        )
        
        metrics['grasp_state'] = self.calculate_metrics(
            self.test_data['y_grasp'],
            y_grasp_pred,
            ["open", "closed", "pinching"]
        )
        
        metrics['interaction_intent'] = self.calculate_metrics(
            self.test_data['y_interaction'],
            y_interaction_pred,
            ["pointing", "manipulating", "resting"]
        )
        
        return metrics
    
    def benchmark_property(self) -> Dict[str, AccuracyMetrics]:
        """Benchmark property prediction accuracy."""
        print("\nBenchmarking property prediction...")
        
        # Get predictions
        X = self.test_data['X']
        
        predictions = self.property_model.predict(X)
        
        # Extract predictions into arrays
        n = len(X)
        y_material_pred = np.zeros((n, 3))
        y_size_pred = np.zeros((n, 3))
        
        for i, pred in enumerate(predictions):
            mat_idx = ["rigid", "soft", "liquid"].index(pred.material)
            size_idx = ["small", "medium", "large"].index(pred.size_category)
            
            y_material_pred[i, mat_idx] = 1.0
            y_size_pred[i, size_idx] = 1.0
        
        # Calculate metrics
        metrics = {}
        
        metrics['material'] = self.calculate_metrics(
            self.test_data['y_material'],
            y_material_pred,
            ["rigid", "soft", "liquid"]
        )
        
        metrics['size_category'] = self.calculate_metrics(
            self.test_data['y_size'],
            y_size_pred,
            ["small", "medium", "large"]
        )
        
        return metrics
    
    def measure_model_sizes(self) -> Dict[str, float]:
        """Measure model sizes."""
        return {
            'intent_model': self.intent_model.get_model_size(),
            'property_model': self.property_model.get_model_size()
        }
    
    def measure_inference_times(self) -> Dict[str, float]:
        """Measure inference times."""
        import tempfile
        
        times = {}
        
        # Create temporary TFLite models
        with tempfile.TemporaryDirectory() as temp_dir:
            # Intent model
            intent_tflite = os.path.join(temp_dir, "intent.tflite")
            self.intent_model.export_tflite(intent_tflite, optimize=False)
            
            engine = EdgeInferenceEngine(
                intent_model_path=intent_tflite,
                mode=InferenceMode.CPU
            )
            
            # Benchmark
            bench = engine.benchmark(num_runs=50, warmup_runs=5)
            times['intent_model'] = bench['mean_ms']
            
            # Property model
            property_tflite = os.path.join(temp_dir, "property.tflite")
            self.property_model.export_tflite(property_tflite, optimize=False)
            
            engine = EdgeInferenceEngine(
                property_model_path=property_tflite,
                mode=InferenceMode.CPU
            )
            
            # Benchmark
            bench = engine.benchmark(num_runs=50, warmup_runs=5)
            times['property_model'] = bench['mean_ms']
        
        return times
    
    def run_full_benchmark(self) -> BenchmarkReport:
        """Run complete accuracy benchmark."""
        print("\n" + "="*70)
        print("RUNNING ACCURACY BENCHMARK")
        print("="*70)
        
        # Benchmark intent classification
        intent_metrics = self.benchmark_intent()
        
        # Calculate overall intent accuracy
        overall_intent_accuracy = np.mean([
            m.accuracy for m in intent_metrics.values()
        ])
        
        # Benchmark property prediction
        property_metrics = self.benchmark_property()
        
        # Calculate overall property accuracy
        overall_property_accuracy = np.mean([
            m.accuracy for m in property_metrics.values()
        ])
        
        # Measure model sizes
        print("\nMeasuring model sizes...")
        model_sizes = self.measure_model_sizes()
        
        # Measure inference times
        print("\nMeasuring inference times...")
        inference_times = self.measure_inference_times()
        
        # Create report
        report = BenchmarkReport(
            intent_metrics=intent_metrics,
            property_metrics=property_metrics,
            overall_intent_accuracy=overall_intent_accuracy,
            overall_property_accuracy=overall_property_accuracy,
            model_sizes_mb=model_sizes,
            inference_times_ms=inference_times
        )
        
        return report


def run_accuracy_benchmark(
    intent_model_path: Optional[str] = None,
    property_model_path: Optional[str] = None,
    dataset_path: Optional[str] = None,
    num_test_samples: int = 1000
) -> BenchmarkReport:
    """
    Run accuracy benchmark with models and dataset.
    
    Args:
        intent_model_path: Path to trained intent model
        property_model_path: Path to trained property model
        dataset_path: Path to test dataset
        num_test_samples: Number of test samples to generate if no dataset
    
    Returns:
        BenchmarkReport with all metrics
    """
    # Load or generate test data
    if dataset_path and os.path.exists(dataset_path):
        print(f"Loading dataset from {dataset_path}")
        dataset = DatasetGenerator.load_dataset(dataset_path)
        test_data = dataset['val']
    else:
        print("Generating synthetic test data...")
        generator = DatasetGenerator(
            image_size=(64, 64),
            num_samples=num_test_samples,
            train_split=0.5,
            seed=42
        )
        dataset = generator.generate_dataset(augment=False)
        test_data = dataset['val']
    
    print(f"Test samples: {len(test_data['X'])}")
    
    # Load or create models
    if intent_model_path and os.path.exists(intent_model_path):
        print(f"Loading intent model from {intent_model_path}")
        intent_model = IntentClassifier.load(intent_model_path)
    else:
        print("Creating new intent model...")
        intent_model = create_intent_classifier()
        intent_model.compile()
        # Quick training for testing
        print("Training intent model (quick)...")
        intent_model.fit(
            dataset['train']['X'][:500],
            {
                'object_type': dataset['train']['y_object'][:500],
                'grasp_state': dataset['train']['y_grasp'][:500],
                'interaction_intent': dataset['train']['y_interaction'][:500]
            },
            epochs=5,
            batch_size=32,
            verbose=0
        )
    
    if property_model_path and os.path.exists(property_model_path):
        print(f"Loading property model from {property_model_path}")
        property_model = PropertyPredictor.load(property_model_path)
    else:
        print("Creating new property model...")
        property_model = create_property_predictor()
        property_model.compile()
        # Quick training for testing
        print("Training property model (quick)...")
        property_model.fit(
            dataset['train']['X'][:500],
            {
                'material': dataset['train']['y_material'][:500],
                'size_category': dataset['train']['y_size'][:500]
            },
            epochs=5,
            batch_size=32,
            verbose=0
        )
    
    # Run benchmark
    benchmark = AccuracyBenchmark(intent_model, property_model, test_data)
    report = benchmark.run_full_benchmark()
    
    return report


def main():
    """Main entry point for benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run accuracy benchmark")
    parser.add_argument("--intent-model", type=str, help="Path to intent model")
    parser.add_argument("--property-model", type=str, help="Path to property model")
    parser.add_argument("--dataset", type=str, help="Path to test dataset")
    parser.add_argument("--output", type=str, default="benchmark_report.json", help="Output path")
    parser.add_argument("--samples", type=int, default=1000, help="Number of test samples")
    
    args = parser.parse_args()
    
    # Run benchmark
    report = run_accuracy_benchmark(
        intent_model_path=args.intent_model,
        property_model_path=args.property_model,
        dataset_path=args.dataset,
        num_test_samples=args.samples
    )
    
    # Print summary
    report.print_summary()
    
    # Save report
    with open(args.output, 'w') as f:
        f.write(report.to_json())
    
    print(f"\n📄 Report saved to {args.output}")
    
    # Return exit code based on targets
    success = (
        report.overall_intent_accuracy > 0.92 and
        report.overall_property_accuracy > 0.90 and
        all(s < 5.0 for s in report.model_sizes_mb.values())
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
"""
Tests for edge inference engine.

Tests TFLite inference, preprocessing, and performance.
"""

from __future__ import annotations

import os
import sys
import unittest
import numpy as np
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.edge_inference import (
    EdgeInferenceEngine, InferenceMode, InferenceResult,
    create_edge_engine
)
from models.intent_classifier import create_intent_classifier
from models.property_predictor import create_property_predictor


class TestEdgeInference(unittest.TestCase):
    """Test cases for edge inference engine."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - create and export models."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export intent model
        intent_model = create_intent_classifier()
        intent_model.compile()
        cls.intent_model_path = os.path.join(cls.temp_dir, "intent_model.tflite")
        intent_model.export_tflite(cls.intent_model_path, optimize=False)
        
        # Create and export property model
        property_model = create_property_predictor()
        property_model.compile()
        cls.property_model_path = os.path.join(cls.temp_dir, "property_model.tflite")
        property_model.export_tflite(cls.property_model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures."""
        shutil.rmtree(cls.temp_dir)
    
    def test_engine_creation(self):
        """Test inference engine can be created."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU,
            num_threads=2
        )
        
        self.assertIsNotNone(engine.intent_interpreter)
        self.assertIsNotNone(engine.property_interpreter)
        self.assertIsNotNone(engine._input_shape)
    
    def test_preprocessing(self):
        """Test input preprocessing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with 2D input
        input_2d = np.random.rand(64, 64).astype(np.float32)
        processed, _ = engine.preprocess(input_2d)
        
        self.assertEqual(len(processed.shape), 4)  # (1, H, W, C)
        self.assertEqual(processed.shape, (1, 64, 64, 1))
        
        # Test with 3D input
        input_3d = np.random.rand(10, 64, 64).astype(np.float32)
        processed, _ = engine.preprocess(input_3d)
        
        self.assertEqual(processed.shape, (10, 64, 64, 1))
    
    def test_intent_inference(self):
        """Test intent classification inference."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.classify_intent(test_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.object_type, ["hand", "tool", "other"])
        self.assertIn(pred.grasp_state, ["open", "closed", "pinching"])
        self.assertIn(pred.interaction_intent, ["pointing", "manipulating", "resting"])
    
    def test_property_inference(self):
        """Test property prediction inference."""
        engine = EdgeInferenceEngine(
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.predict_properties(test_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.material, ["rigid", "soft", "liquid"])
        self.assertIn(pred.size_category, ["small", "medium", "large"])
        
        # Check probability dictionaries
        self.assertEqual(len(pred.material_probabilities), 3)
        self.assertEqual(len(pred.size_probabilities), 3)
    
    def test_full_inference(self):
        """Test complete inference pipeline."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create test input
        test_input = np.random.rand(64, 64).astype(np.float32)
        
        # Run inference
        result = engine.infer(test_input, run_intent=True, run_property=True)
        
        # Check result
        self.assertIsInstance(result, InferenceResult)
        self.assertIsNotNone(result.intent)
        self.assertIsNotNone(result.properties)
        self.assertGreater(result.inference_time_ms, 0)
        self.assertGreater(result.total_time_ms, 0)
    
    def test_inference_modes(self):
        """Test different inference modes."""
        for mode in [InferenceMode.CPU, InferenceMode.AUTO]:
            engine = EdgeInferenceEngine(
                intent_model_path=self.intent_model_path,
                mode=mode,
                num_threads=2
            )
            
            test_input = np.random.rand(64, 64).astype(np.float32)
            result = engine.infer(test_input, run_intent=True, run_property=False)
            
            self.assertIsNotNone(result.intent)
    
    def test_batch_processing(self):
        """Test batch processing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            mode=InferenceMode.CPU
        )
        
        # Create batch input
        batch_size = 5
        test_input = np.random.rand(batch_size, 64, 64, 1).astype(np.float32)
        
        # Run inference
        predictions = engine.classify_intent(test_input)
        
        # Check output
        self.assertEqual(len(predictions), batch_size)
    
    def test_model_info(self):
        """Test getting model information."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        info = engine.get_model_info()
        
        self.assertIn('intent_model_loaded', info)
        self.assertIn('property_model_loaded', info)
        self.assertIn('input_shape', info)
        self.assertIn('mode', info)
        
        self.assertTrue(info['intent_model_loaded'])
        self.assertTrue(info['property_model_loaded'])
    
    def test_benchmark(self):
        """Test benchmark functionality."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_model_path,
            property_model_path=self.property_model_path,
            mode=InferenceMode.CPU
        )
        
        # Run short benchmark
        results = engine.benchmark(num_runs=10, warmup_runs=2)
        
        # Check results
        self.assertIn('mean_ms', results)
        self.assertIn('std_ms', results)
        self.assertIn('min_ms', results)
        self.assertIn('max_ms', results)
        self.assertIn('throughput_fps', results)
        
        # All values should be positive
        for key, value in results.items():
            self.assertGreaterEqual(value, 0)


class TestInferenceModes(unittest.TestCase):
    """Test different inference execution modes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export model
        model = create_intent_classifier()
        model.compile()
        cls.model_path = os.path.join(cls.temp_dir, "test_model.tflite")
        model.export_tflite(cls.model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_cpu_mode(self):
        """Test CPU inference mode."""
        engine = create_edge_engine(
            intent_model=self.model_path,
            mode="cpu",
            num_threads=2
        )
        
        test_input = np.random.rand(64, 64).astype(np.float32)
        result = engine.infer(test_input)
        
        self.assertIsNotNone(result.intent)
    
    def test_auto_mode(self):
        """Test auto inference mode."""
        engine = create_edge_engine(
            intent_model=self.model_path,
            mode="auto"
        )
        
        test_input = np.random.rand(64, 64).astype(np.float32)
        result = engine.infer(test_input)
        
        self.assertIsNotNone(result.intent)


class TestInferencePerformance(unittest.TestCase):
    """Performance tests for inference."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create and export models
        intent_model = create_intent_classifier()
        intent_model.compile()
        cls.intent_path = os.path.join(cls.temp_dir, "intent.tflite")
        intent_model.export_tflite(cls.intent_path, optimize=False)
        
        property_model = create_property_predictor()
        property_model.compile()
        cls.property_path = os.path.join(cls.temp_dir, "property.tflite")
        property_model.export_tflite(cls.property_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_inference_latency(self):
        """Test inference meets latency requirements."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_path,
            property_model_path=self.property_path,
            mode=InferenceMode.CPU
        )
        
        # Run benchmark
        results = engine.benchmark(num_runs=50, warmup_runs=5)
        
        # Check mean latency (should be < 50ms on CPU for testing)
        # On actual NPU, this would be < 5ms
        mean_latency = results['mean_ms']
        print(f"\nMean inference latency: {mean_latency:.2f} ms")
        
        self.assertLess(mean_latency, 100)  # Relaxed for CPU testing
    
    def test_throughput(self):
        """Test inference throughput."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.intent_path,
            mode=InferenceMode.CPU
        )
        
        # Run benchmark
        results = engine.benchmark(num_runs=50, warmup_runs=5)
        
        # Check throughput (should be > 10 FPS)
        throughput = results['throughput_fps']
        print(f"\nInference throughput: {throughput:.1f} FPS")
        
        self.assertGreater(throughput, 5)  # Relaxed for CPU testing


class TestPreprocessing(unittest.TestCase):
    """Tests for input preprocessing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        
        model = create_intent_classifier()
        model.compile()
        cls.model_path = os.path.join(cls.temp_dir, "test.tflite")
        model.export_tflite(cls.model_path, optimize=False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.temp_dir)
    
    def test_normalization(self):
        """Test input normalization."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with high values
        high_input = np.ones((64, 64)) * 255.0
        processed, _ = engine.preprocess(high_input, normalize=True)
        
        # Should be normalized to [0, 1]
        self.assertLessEqual(processed.max(), 1.0)
        self.assertGreaterEqual(processed.min(), 0.0)
    
    def test_resize(self):
        """Test input resizing."""
        engine = EdgeInferenceEngine(
            intent_model_path=self.model_path,
            mode=InferenceMode.CPU
        )
        
        # Test with different size
        large_input = np.random.rand(128, 128).astype(np.float32)
        processed, _ = engine.preprocess(large_input, resize=True)
        
        # Should be resized to model input shape
        self.assertEqual(processed.shape[1:3], (64, 64))


def run_tests():
    """Run all inference tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeInference))
    suite.addTests(loader.loadTestsFromTestCase(TestInferenceModes))
    suite.addTests(loader.loadTestsFromTestCase(TestInferencePerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestPreprocessing))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
"""
Unit Tests for Intent Classification Model
==========================================

Tests for model architecture, training, and inference.
Run with: pytest tests/test_model.py -v
"""

import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from model import IntentClassifier, ModelConfig


class TestModelArchitecture:
    """Test model architecture and configuration."""
    
    def test_model_creation(self):
        """Test model can be created."""
        classifier = IntentClassifier()
        assert classifier.model is not None
    
    def test_model_config(self):
        """Test custom configuration."""
        config = ModelConfig(input_points=32, num_classes=5)
        classifier = IntentClassifier(config)
        
        assert classifier.config.input_points == 32
        assert classifier.config.num_classes == 5
    
    def test_model_size(self):
        """Test model size is under limit."""
        classifier = IntentClassifier()
        size_kb = classifier.get_model_size_kb()
        
        # Model should be under 1MB (1024 KB)
        assert size_kb < 1024, f"Model too large: {size_kb:.2f} KB"
    
    def test_parameter_count(self):
        """Test parameter count is reasonable."""
        classifier = IntentClassifier()
        params = classifier.count_parameters()
        
        # Should have parameters but not too many
        assert params > 1000
        assert params < 500000


class TestModelPrediction:
    """Test model prediction functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier fixture."""
        return IntentClassifier()
    
    @pytest.fixture
    def sample_contour(self):
        """Create sample contour fixture."""
        np.random.seed(42)
        return np.random.randn(64, 3).astype(np.float32)
    
    def test_prediction_output_shape(self, classifier, sample_contour):
        """Test prediction returns correct output."""
        result = classifier.predict(sample_contour)
        
        assert 'class' in result
        assert 'confidence' in result
        assert 'probabilities' in result
        assert result['class'] in ['hand', 'tool', 'other']
    
    def test_prediction_probabilities_sum(self, classifier, sample_contour):
        """Test probabilities sum to 1."""
        result = classifier.predict(sample_contour)
        probs = result['probabilities']
        
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01
    
    def test_prediction_confidence_range(self, classifier, sample_contour):
        """Test confidence is in valid range."""
        result = classifier.predict(sample_contour)
        
        assert 0 <= result['confidence'] <= 1
    
    def test_batch_prediction(self, classifier):
        """Test prediction on batch."""
        batch = np.random.randn(10, 64, 3).astype(np.float32)
        
        # Should work with batch dimension
        result = classifier.predict(batch[0])
        assert result['class'] in ['hand', 'tool', 'other']


class TestModelTraining:
    """Test model training functionality."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample training data."""
        np.random.seed(42)
        n_samples = 100
        
        X = np.random.randn(n_samples, 64, 3).astype(np.float32)
        y = np.zeros((n_samples, 3))
        
        # Random labels
        for i in range(n_samples):
            y[i, i % 3] = 1
        
        return X, y
    
    def test_training_runs(self, sample_data):
        """Test training executes without error."""
        X, y = sample_data
        
        # Split
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        classifier = IntentClassifier()
        
        # Train for just 2 epochs (fast test)
        history = classifier.train(
            X_train, y_train,
            X_val, y_val,
            epochs=2,
            batch_size=16
        )
        
        assert 'accuracy' in history.history
        assert len(history.history['accuracy']) == 2
    
    def test_evaluation(self, sample_data):
        """Test model evaluation."""
        X, y = sample_data
        
        classifier = IntentClassifier()
        metrics = classifier.evaluate(X, y)
        
        assert 'accuracy' in metrics
        assert 'loss' in metrics
        assert 0 <= metrics['accuracy'] <= 1


class TestModelSaveLoad:
    """Test model save and load functionality."""
    
    @pytest.fixture
    def temp_model_path(self, tmp_path):
        """Create temporary model path."""
        return str(tmp_path / "test_model.keras")
    
    def test_save_load(self, temp_model_path):
        """Test model can be saved and loaded."""
        # Create and save
        original = IntentClassifier()
        original.save(temp_model_path)
        
        assert os.path.exists(temp_model_path)
        
        # Load
        loaded = IntentClassifier.load(temp_model_path)
        
        assert loaded.model is not None
        assert loaded.class_names == original.class_names
    
    def test_save_load_prediction_consistency(self, temp_model_path):
        """Test predictions are consistent after save/load."""
        np.random.seed(42)
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Create, save, and load
        original = IntentClassifier()
        original.save(temp_model_path)
        loaded = IntentClassifier.load(temp_model_path)
        
        # Both should produce same class (not necessarily same confidence)
        pred_original = original.predict(test_contour)
        pred_loaded = loaded.predict(test_contour)
        
        assert pred_original['class'] == pred_loaded['class']


class TestPerformance:
    """Test model performance characteristics."""
    
    def test_inference_latency(self):
        """Test inference latency is under target."""
        import time
        
        classifier = IntentClassifier()
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Warm-up
        for _ in range(10):
            classifier.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(50):
            start = time.perf_counter()
            classifier.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        mean_latency = np.mean(times)
        
        # Should be under 10ms (generous for test environment)
        assert mean_latency < 10, f"Latency too high: {mean_latency:.2f}ms"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()
"""
Unit tests for Shadow Intelligence Layer models.

Tests model architecture, training, and prediction functionality.
"""

from __future__ import annotations

import os
import sys
import unittest
import numpy as np
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.intent_classifier import (
    IntentClassifier, ModelConfig, create_intent_classifier
)
from models.property_predictor import (
    PropertyPredictor, PropertyModelConfig, create_property_predictor
)


class TestIntentClassifier(unittest.TestCase):
    """Test cases for intent classifier."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = ModelConfig(
            input_shape=(64, 64, 1),
            dropout_rate=0.3,
            use_separable_conv=True
        )
        cls.model = IntentClassifier(cls.config)
    
    def test_model_creation(self):
        """Test model can be created."""
        self.assertIsNotNone(self.model.model)
        self.assertIsNotNone(self.model.config)
    
    def test_model_architecture(self):
        """Test model architecture is correct."""
        # Check input shape
        self.assertEqual(
            self.model.model.input_shape,
            (None, 64, 64, 1)
        )
        
        # Check output shapes
        outputs = self.model.model.outputs
        self.assertEqual(len(outputs), 3)
        
        # Object type output
        self.assertEqual(outputs[0].shape[-1], 3)
        # Grasp state output
        self.assertEqual(outputs[1].shape[-1], 3)
        # Interaction intent output
        self.assertEqual(outputs[2].shape[-1], 3)
    
    def test_model_compilation(self):
        """Test model can be compiled."""
        try:
            self.model.compile()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Model compilation failed: {e}")
    
    def test_prediction_shape(self):
        """Test prediction output shape."""
        self.model.compile()
        
        # Create dummy input
        dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.object_type, ["hand", "tool", "other"])
        self.assertIn(pred.grasp_state, ["open", "closed", "pinching"])
        self.assertIn(pred.interaction_intent, ["pointing", "manipulating", "resting"])
        
        # Check confidence values
        self.assertGreaterEqual(pred.object_confidence, 0.0)
        self.assertLessEqual(pred.object_confidence, 1.0)
        self.assertGreaterEqual(pred.overall_confidence, 0.0)
        self.assertLessEqual(pred.overall_confidence, 1.0)
    
    def test_batch_prediction(self):
        """Test batch prediction."""
        self.model.compile()
        
        # Create batch input
        batch_size = 5
        dummy_input = np.random.rand(batch_size, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), batch_size)
    
    def test_model_parameters(self):
        """Test model parameter count."""
        param_count = self.model.count_parameters()
        
        # Model should be lightweight (< 1M params)
        self.assertLess(param_count, 1_000_000)
        print(f"Intent model parameters: {param_count:,}")
    
    def test_model_save_load(self):
        """Test model save and load."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save model
            save_path = os.path.join(temp_dir, "test_model.keras")
            self.model.save(save_path)
            
            # Check file exists
            self.assertTrue(os.path.exists(save_path))
            
            # Load model
            loaded_model = IntentClassifier.load(save_path)
            
            # Check loaded model works
            self.assertIsNotNone(loaded_model.model)
            
            # Test prediction
            dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
            predictions = loaded_model.predict(dummy_input)
            self.assertEqual(len(predictions), 1)
        
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
    
    def test_tflite_export(self):
        """Test TFLite export."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Export
            tflite_path = os.path.join(temp_dir, "test_model.tflite")
            self.model.export_tflite(tflite_path, optimize=False)
            
            # Check file exists and has content
            self.assertTrue(os.path.exists(tflite_path))
            self.assertGreater(os.path.getsize(tflite_path), 0)
            
            # Check size is reasonable (< 5MB)
            size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
            self.assertLess(size_mb, 5.0)
            print(f"TFLite model size: {size_mb:.2f} MB")
        
        finally:
            shutil.rmtree(temp_dir)


class TestPropertyPredictor(unittest.TestCase):
    """Test cases for property predictor."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = PropertyModelConfig(
            input_shape=(64, 64, 1),
            dropout_rate=0.25,
            use_separable_conv=True
        )
        cls.model = PropertyPredictor(cls.config)
    
    def test_model_creation(self):
        """Test model can be created."""
        self.assertIsNotNone(self.model.model)
        self.assertIsNotNone(self.model.config)
    
    def test_model_architecture(self):
        """Test model architecture is correct."""
        # Check input shape
        self.assertEqual(
            self.model.model.input_shape,
            (None, 64, 64, 1)
        )
        
        # Check output shapes
        outputs = self.model.model.outputs
        self.assertEqual(len(outputs), 2)
        
        # Material output
        self.assertEqual(outputs[0].shape[-1], 3)
        # Size category output
        self.assertEqual(outputs[1].shape[-1], 3)
    
    def test_prediction_shape(self):
        """Test prediction output shape."""
        self.model.compile()
        
        # Create dummy input
        dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
        
        # Predict
        predictions = self.model.predict(dummy_input)
        
        # Check output
        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        
        self.assertIn(pred.material, ["rigid", "soft", "liquid"])
        self.assertIn(pred.size_category, ["small", "medium", "large"])
        
        # Check confidence values
        self.assertGreaterEqual(pred.material_confidence, 0.0)
        self.assertLessEqual(pred.material_confidence, 1.0)
        self.assertGreaterEqual(pred.overall_confidence, 0.0)
        self.assertLessEqual(pred.overall_confidence, 1.0)
        
        # Check probability dictionaries
        self.assertEqual(len(pred.material_probabilities), 3)
        self.assertEqual(len(pred.size_probabilities), 3)
    
    def test_model_parameters(self):
        """Test model parameter count."""
        param_count = self.model.count_parameters()
        
        # Model should be lightweight (< 500K params)
        self.assertLess(param_count, 500_000)
        print(f"Property model parameters: {param_count:,}")
    
    def test_model_save_load(self):
        """Test model save and load."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save model
            save_path = os.path.join(temp_dir, "test_property_model.keras")
            self.model.save(save_path)
            
            # Load model
            loaded_model = PropertyPredictor.load(save_path)
            
            # Test prediction
            dummy_input = np.random.rand(1, 64, 64, 1).astype(np.float32)
            predictions = loaded_model.predict(dummy_input)
            self.assertEqual(len(predictions), 1)
        
        finally:
            shutil.rmtree(temp_dir)


class TestModelIntegration(unittest.TestCase):
    """Integration tests for both models."""
    
    def test_models_work_together(self):
        """Test both models can work with same input."""
        # Create models
        intent_model = create_intent_classifier()
        property_model = create_property_predictor()
        
        # Compile
        intent_model.compile()
        property_model.compile()
        
        # Create shared input
        dummy_input = np.random.rand(5, 64, 64, 1).astype(np.float32)
        
        # Run both predictions
        intent_preds = intent_model.predict(dummy_input)
        property_preds = property_model.predict(dummy_input)
        
        # Check outputs match
        self.assertEqual(len(intent_preds), len(property_preds))
        self.assertEqual(len(intent_preds), 5)
    
    def test_model_sizes(self):
        """Test combined model sizes."""
        intent_model = create_intent_classifier()
        property_model = create_property_predictor()
        
        intent_params = intent_model.count_parameters()
        property_params = property_model.count_parameters()
        total_params = intent_params + property_params
        
        # Combined should be < 1.5M params
        self.assertLess(total_params, 1_500_000)
        print(f"\nTotal parameters: {total_params:,}")
        print(f"  Intent: {intent_params:,}")
        print(f"  Property: {property_params:,}")


class TestModelTraining(unittest.TestCase):
    """Tests for model training functionality."""
    
    def test_intent_training(self):
        """Test intent model can be trained."""
        model = create_intent_classifier()
        model.compile()
        
        # Create small synthetic dataset
        n_samples = 50
        X = np.random.rand(n_samples, 64, 64, 1).astype(np.float32)
        
        y = {
            "object_type": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "grasp_state": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "interaction_intent": np.eye(3)[np.random.randint(0, 3, n_samples)]
        }
        
        # Train for a few epochs
        history = model.fit(
            X, y,
            epochs=2,
            batch_size=10,
            verbose=0
        )
        
        # Check history has expected keys
        self.assertIn('loss', history)
        self.assertIn('object_type_accuracy', history)
    
    def test_property_training(self):
        """Test property model can be trained."""
        model = create_property_predictor()
        model.compile()
        
        # Create small synthetic dataset
        n_samples = 50
        X = np.random.rand(n_samples, 64, 64, 1).astype(np.float32)
        
        y = {
            "material": np.eye(3)[np.random.randint(0, 3, n_samples)],
            "size_category": np.eye(3)[np.random.randint(0, 3, n_samples)]
        }
        
        # Train for a few epochs
        history = model.fit(
            X, y,
            epochs=2,
            batch_size=10,
            verbose=0
        )
        
        # Check history has expected keys
        self.assertIn('loss', history)
        self.assertIn('material_accuracy', history)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntentClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestPropertyPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestModelIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestModelTraining))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
"""
Models package for Shadow Intelligence Layer.
"""

from models.intent_classifier import (
    IntentClassifier,
    ModelConfig,
    IntentPrediction,
    create_intent_classifier
)

from models.property_predictor import (
    PropertyPredictor,
    PropertyModelConfig,
    PropertyPrediction,
    create_property_predictor
)

__all__ = [
    'IntentClassifier',
    'ModelConfig',
    'IntentPrediction',
    'create_intent_classifier',
    'PropertyPredictor',
    'PropertyModelConfig',
    'PropertyPrediction',
    'create_property_predictor'
]
"""
Intent Classification Model for Shadow Intelligence Layer.

Lightweight CNN for classifying:
- Object type: human hand, tool, other object
- Grasping state: open, closed, pinching
- Interaction intent: pointing, manipulating, resting

Target: <5MB model, >92% accuracy, <5ms inference on Snapdragon 8 Gen 3 NPU
"""

from __future__ import annotations

import numpy as np
import tensorflow as tf
from tensorflow import keras
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any
import json


@dataclass
class IntentPrediction:
    """Structured output for intent classification."""
    object_type: str
    object_confidence: float
    grasp_state: str
    grasp_confidence: float
    interaction_intent: str
    interaction_confidence: float
    overall_confidence: float
    raw_logits: Dict[str, np.ndarray]


@dataclass
class ModelConfig:
    """Configuration for the intent classifier."""
    input_shape: Tuple[int, int, int] = (64, 64, 1)
    num_object_types: int = 3  # hand, tool, other
    num_grasp_states: int = 3  # open, closed, pinching
    num_interaction_intents: int = 3  # pointing, manipulating, resting
    dropout_rate: float = 0.3
    use_separable_conv: bool = True  # For smaller model size
    
    # Class labels
    object_types: List[str] = None
    grasp_states: List[str] = None
    interaction_intents: List[str] = None
    
    def __post_init__(self):
        if self.object_types is None:
            self.object_types = ["hand", "tool", "other"]
        if self.grasp_states is None:
            self.grasp_states = ["open", "closed", "pinching"]
        if self.interaction_intents is None:
            self.interaction_intents = ["pointing", "manipulating", "resting"]


class IntentClassifier:
    """
    Lightweight CNN for intent classification from shadow data.
    
    Architecture optimized for edge deployment:
    - Depthwise separable convolutions for efficiency
    - Global average pooling instead of flatten
    - Multi-head output for different prediction tasks
    """
    
    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        """Initialize the intent classifier."""
        self.config = config or ModelConfig()
        self.model: Optional[keras.Model] = None
        self._build_model()
    
    def _build_model(self) -> None:
        """Build the lightweight CNN architecture."""
        cfg = self.config
        inputs = keras.Input(shape=cfg.input_shape, name="shadow_input")
        
        x = inputs
        
        # Block 1: Initial feature extraction
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="sepconv1"
            )(x)
        else:
            x = keras.layers.Conv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="conv1"
            )(x)
        x = keras.layers.BatchNormalization(name="bn1")(x)
        x = keras.layers.ReLU(name="relu1")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool1")(x)  # 32x32
        
        # Block 2: Deeper features
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="sepconv2"
            )(x)
        else:
            x = keras.layers.Conv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="conv2"
            )(x)
        x = keras.layers.BatchNormalization(name="bn2")(x)
        x = keras.layers.ReLU(name="relu2")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool2")(x)  # 16x16
        
        # Block 3: High-level features
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                128, (3, 3), padding='same', use_bias=False,
                name="sepconv3"
            )(x)
        else:
            x = keras.layers.Conv2D(
                128, (3, 3), padding='same', use_bias=False,
                name="conv3"
            )(x)
        x = keras.layers.BatchNormalization(name="bn3")(x)
        x = keras.layers.ReLU(name="relu3")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool3")(x)  # 8x8
        
        # Block 4: Final feature extraction
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                256, (3, 3), padding='same', use_bias=False,
                name="sepconv4"
            )(x)
        else:
            x = keras.layers.Conv2D(
                256, (3, 3), padding='same', use_bias=False,
                name="conv4"
            )(x)
        x = keras.layers.BatchNormalization(name="bn4")(x)
        x = keras.layers.ReLU(name="relu4")(x)
        
        # Global average pooling for efficiency
        x = keras.layers.GlobalAveragePooling2D(name="gap")(x)
        
        # Shared dense layer
        x = keras.layers.Dense(128, use_bias=False, name="dense_shared")(x)
        x = keras.layers.BatchNormalization(name="bn_shared")(x)
        x = keras.layers.ReLU(name="relu_shared")(x)
        x = keras.layers.Dropout(cfg.dropout_rate, name="dropout")(x)
        
        # Multi-head outputs
        # Object type classification
        object_out = keras.layers.Dense(
            cfg.num_object_types, activation='softmax',
            name="object_type"
        )(x)
        
        # Grasp state classification
        grasp_out = keras.layers.Dense(
            cfg.num_grasp_states, activation='softmax',
            name="grasp_state"
        )(x)
        
        # Interaction intent classification
        interaction_out = keras.layers.Dense(
            cfg.num_interaction_intents, activation='softmax',
            name="interaction_intent"
        )(x)
        
        self.model = keras.Model(
            inputs=inputs,
            outputs=[object_out, grasp_out, interaction_out],
            name="intent_classifier"
        )
    
    def compile(
        self,
        optimizer: Optional[keras.optimizers.Optimizer] = None,
        loss_weights: Optional[Dict[str, float]] = None
    ) -> None:
        """Compile the model with multi-task loss."""
        if optimizer is None:
            optimizer = keras.optimizers.Adam(learning_rate=0.001)
        
        if loss_weights is None:
            loss_weights = {
                "object_type": 1.0,
                "grasp_state": 1.0,
                "interaction_intent": 1.0
            }
        
        self.model.compile(
            optimizer=optimizer,
            loss={
                "object_type": "categorical_crossentropy",
                "grasp_state": "categorical_crossentropy",
                "interaction_intent": "categorical_crossentropy"
            },
            loss_weights=loss_weights,
            metrics={
                "object_type": ["accuracy"],
                "grasp_state": ["accuracy"],
                "interaction_intent": ["accuracy"]
            }
        )
    
    def fit(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray],
        validation_data: Optional[Tuple[np.ndarray, Dict[str, np.ndarray]]] = None,
        epochs: int = 50,
        batch_size: int = 32,
        callbacks: Optional[List[keras.callbacks.Callback]] = None,
        **kwargs
    ) -> keras.callbacks.History:
        """Train the model."""
        if callbacks is None:
            callbacks = self._get_default_callbacks()
        
        return self.model.fit(
            x, y,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            **kwargs
        )
    
    def _get_default_callbacks(self) -> List[keras.callbacks.Callback]:
        """Get default training callbacks."""
        return [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
    
    def predict(self, x: np.ndarray) -> List[IntentPrediction]:
        """
        Predict intent from shadow data.
        
        Args:
            x: Input array of shape (N, H, W, C) or (H, W, C)
        
        Returns:
            List of IntentPrediction objects
        """
        # Ensure batch dimension
        if len(x.shape) == 3:
            x = np.expand_dims(x, axis=0)
        
        # Get predictions
        object_pred, grasp_pred, interaction_pred = self.model.predict(x, verbose=0)
        
        # Convert to structured output
        predictions = []
        for i in range(len(x)):
            obj_idx = np.argmax(object_pred[i])
            grasp_idx = np.argmax(grasp_pred[i])
            interaction_idx = np.argmax(interaction_pred[i])
            
            pred = IntentPrediction(
                object_type=self.config.object_types[obj_idx],
                object_confidence=float(object_pred[i][obj_idx]),
                grasp_state=self.config.grasp_states[grasp_idx],
                grasp_confidence=float(grasp_pred[i][grasp_idx]),
                interaction_intent=self.config.interaction_intents[interaction_idx],
                interaction_confidence=float(interaction_pred[i][interaction_idx]),
                overall_confidence=float(
                    object_pred[i][obj_idx] * 
                    grasp_pred[i][grasp_idx] * 
                    interaction_pred[i][interaction_idx]
                ),
                raw_logits={
                    "object_type": object_pred[i],
                    "grasp_state": grasp_pred[i],
                    "interaction_intent": interaction_pred[i]
                }
            )
            predictions.append(pred)
        
        return predictions
    
    def evaluate(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Evaluate model performance."""
        results = self.model.evaluate(x, y, verbose=0, return_dict=True)
        return results
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        self.model.save(path)
        # Save config separately
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'input_shape': self.config.input_shape,
                'object_types': self.config.object_types,
                'grasp_states': self.config.grasp_states,
                'interaction_intents': self.config.interaction_intents
            }, f)
    
    @classmethod
    def load(cls, path: str) -> "IntentClassifier":
        """Load model from disk."""
        # Load config
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            config = ModelConfig(
                input_shape=tuple(config_dict['input_shape']),
                object_types=config_dict['object_types'],
                grasp_states=config_dict['grasp_states'],
                interaction_intents=config_dict['interaction_intents']
            )
        except FileNotFoundError:
            config = ModelConfig()
        
        # Create instance and load weights
        instance = cls(config)
        instance.model = keras.models.load_model(path)
        return instance
    
    def export_tflite(
        self,
        path: str,
        optimize: bool = True,
        representative_dataset: Optional[Callable] = None
    ) -> None:
        """
        Export model to TensorFlow Lite format.
        
        Args:
            path: Output path for .tflite file
            optimize: Whether to apply optimizations
            representative_dataset: Dataset for full integer quantization
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if optimize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            if representative_dataset is not None:
                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [
                    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
                ]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        with open(path, 'wb') as f:
            f.write(tflite_model)
        
        # Log model size
        size_mb = len(tflite_model) / (1024 * 1024)
        print(f"TFLite model exported: {path}")
        print(f"Model size: {size_mb:.2f} MB")
    
    def get_model_size(self) -> float:
        """Get model size in MB."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as f:
            temp_path = f.name
        
        self.save(temp_path)
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        os.remove(temp_path)
        
        return size_mb
    
    def summary(self) -> None:
        """Print model summary."""
        self.model.summary()
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return self.model.count_params()


def create_intent_classifier(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    **kwargs
) -> IntentClassifier:
    """Factory function to create an intent classifier."""
    config = ModelConfig(input_shape=input_shape, **kwargs)
    return IntentClassifier(config)
{
  "created_at": "2026-03-19T02:54:47.221866",
  "n_samples": 2000,
  "epochs_trained": 20,
  "train_accuracy": 0.9993749856948853,
  "val_accuracy": 1.0,
  "model_size_mb": 0.2774772644042969,
  "target_accuracy": 0.92,
  "target_met": true,
  "config": {
    "contour_points": 64,
    "num_classes": 3,
    "class_names": [
      "hand",
      "tool",
      "other"
    ]
  }
}
"""
Property Prediction Model for Shadow Intelligence Layer.

Lightweight model for predicting object properties:
- Material type: rigid, soft, liquid
- Size category: small, medium, large
- Confidence scores for each prediction

Target: <2MB model, >90% accuracy, <3ms inference on Snapdragon 8 Gen 3 NPU
"""

from __future__ import annotations

import numpy as np
import tensorflow as tf
from tensorflow import keras
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any
import json


@dataclass
class PropertyPrediction:
    """Structured output for property prediction."""
    material: str
    material_confidence: float
    size_category: str
    size_confidence: float
    material_probabilities: Dict[str, float]
    size_probabilities: Dict[str, float]
    overall_confidence: float


@dataclass
class PropertyModelConfig:
    """Configuration for the property predictor."""
    input_shape: Tuple[int, int, int] = (64, 64, 1)
    num_materials: int = 3  # rigid, soft, liquid
    num_sizes: int = 3  # small, medium, large
    dropout_rate: float = 0.25
    use_separable_conv: bool = True
    
    # Class labels
    materials: List[str] = None
    size_categories: List[str] = None
    
    def __post_init__(self):
        if self.materials is None:
            self.materials = ["rigid", "soft", "liquid"]
        if self.size_categories is None:
            self.size_categories = ["small", "medium", "large"]


class PropertyPredictor:
    """
    Lightweight model for predicting object properties from shadow data.
    
    Uses efficient architecture with depthwise separable convolutions
    for minimal model size and fast inference on edge devices.
    """
    
    def __init__(self, config: Optional[PropertyModelConfig] = None) -> None:
        """Initialize the property predictor."""
        self.config = config or PropertyModelConfig()
        self.model: Optional[keras.Model] = None
        self._build_model()
    
    def _build_model(self) -> None:
        """Build the lightweight property prediction architecture."""
        cfg = self.config
        inputs = keras.Input(shape=cfg.input_shape, name="shadow_input")
        
        x = inputs
        
        # Block 1: Initial feature extraction (32 filters)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="sepconv1"
            )(x)
        else:
            x = keras.layers.Conv2D(
                32, (3, 3), padding='same', use_bias=False,
                name="conv1"
            )(x)
        x = keras.layers.BatchNormalization(name="bn1")(x)
        x = keras.layers.ReLU(name="relu1")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool1")(x)  # 32x32
        
        # Block 2: Deeper features (64 filters)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="sepconv2"
            )(x)
        else:
            x = keras.layers.Conv2D(
                64, (3, 3), padding='same', use_bias=False,
                name="conv2"
            )(x)
        x = keras.layers.BatchNormalization(name="bn2")(x)
        x = keras.layers.ReLU(name="relu2")(x)
        x = keras.layers.MaxPooling2D((2, 2), name="pool2")(x)  # 16x16
        
        # Block 3: High-level features (96 filters - smaller than intent model)
        if cfg.use_separable_conv:
            x = keras.layers.SeparableConv2D(
                96, (3, 3), padding='same', use_bias=False,
                name="sepconv3"
            )(x)
        else:
            x = keras.layers.Conv2D(
                96, (3, 3), padding='same', use_bias=False,
                name="conv3"
            )(x)
        x = keras.layers.BatchNormalization(name="bn3")(x)
        x = keras.layers.ReLU(name="relu3")(x)
        
        # Global average pooling
        x = keras.layers.GlobalAveragePooling2D(name="gap")(x)
        
        # Shared dense layer (smaller than intent model)
        x = keras.layers.Dense(64, use_bias=False, name="dense_shared")(x)
        x = keras.layers.BatchNormalization(name="bn_shared")(x)
        x = keras.layers.ReLU(name="relu_shared")(x)
        x = keras.layers.Dropout(cfg.dropout_rate, name="dropout")(x)
        
        # Multi-head outputs
        # Material classification
        material_out = keras.layers.Dense(
            cfg.num_materials, activation='softmax',
            name="material"
        )(x)
        
        # Size category classification
        size_out = keras.layers.Dense(
            cfg.num_sizes, activation='softmax',
            name="size_category"
        )(x)
        
        self.model = keras.Model(
            inputs=inputs,
            outputs=[material_out, size_out],
            name="property_predictor"
        )
    
    def compile(
        self,
        optimizer: Optional[keras.optimizers.Optimizer] = None,
        loss_weights: Optional[Dict[str, float]] = None
    ) -> None:
        """Compile the model with multi-task loss."""
        if optimizer is None:
            optimizer = keras.optimizers.Adam(learning_rate=0.001)
        
        if loss_weights is None:
            loss_weights = {
                "material": 1.0,
                "size_category": 1.0
            }
        
        self.model.compile(
            optimizer=optimizer,
            loss={
                "material": "categorical_crossentropy",
                "size_category": "categorical_crossentropy"
            },
            loss_weights=loss_weights,
            metrics={
                "material": ["accuracy"],
                "size_category": ["accuracy"]
            }
        )
    
    def fit(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray],
        validation_data: Optional[Tuple[np.ndarray, Dict[str, np.ndarray]]] = None,
        epochs: int = 50,
        batch_size: int = 32,
        callbacks: Optional[List[keras.callbacks.Callback]] = None,
        **kwargs
    ) -> keras.callbacks.History:
        """Train the model."""
        if callbacks is None:
            callbacks = self._get_default_callbacks()
        
        return self.model.fit(
            x, y,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            **kwargs
        )
    
    def _get_default_callbacks(self) -> List[keras.callbacks.Callback]:
        """Get default training callbacks."""
        return [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
    
    def predict(self, x: np.ndarray) -> List[PropertyPrediction]:
        """
        Predict properties from shadow data.
        
        Args:
            x: Input array of shape (N, H, W, C) or (H, W, C)
        
        Returns:
            List of PropertyPrediction objects
        """
        # Ensure batch dimension
        if len(x.shape) == 3:
            x = np.expand_dims(x, axis=0)
        
        # Get predictions
        material_pred, size_pred = self.model.predict(x, verbose=0)
        
        # Convert to structured output
        predictions = []
        cfg = self.config
        for i in range(len(x)):
            mat_idx = np.argmax(material_pred[i])
            size_idx = np.argmax(size_pred[i])
            
            # Build probability dictionaries
            mat_probs = {
                cfg.materials[j]: float(material_pred[i][j])
                for j in range(len(cfg.materials))
            }
            size_probs = {
                cfg.size_categories[j]: float(size_pred[i][j])
                for j in range(len(cfg.size_categories))
            }
            
            pred = PropertyPrediction(
                material=cfg.materials[mat_idx],
                material_confidence=float(material_pred[i][mat_idx]),
                size_category=cfg.size_categories[size_idx],
                size_confidence=float(size_pred[i][size_idx]),
                material_probabilities=mat_probs,
                size_probabilities=size_probs,
                overall_confidence=float(
                    material_pred[i][mat_idx] * size_pred[i][size_idx]
                )
            )
            predictions.append(pred)
        
        return predictions
    
    def evaluate(
        self,
        x: np.ndarray,
        y: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Evaluate model performance."""
        results = self.model.evaluate(x, y, verbose=0, return_dict=True)
        return results
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        self.model.save(path)
        # Save config separately
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                'input_shape': self.config.input_shape,
                'materials': self.config.materials,
                'size_categories': self.config.size_categories
            }, f)
    
    @classmethod
    def load(cls, path: str) -> "PropertyPredictor":
        """Load model from disk."""
        # Load config
        config_path = path.replace('.keras', '_config.json').replace('.h5', '_config.json')
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            config = PropertyModelConfig(
                input_shape=tuple(config_dict['input_shape']),
                materials=config_dict['materials'],
                size_categories=config_dict['size_categories']
            )
        except FileNotFoundError:
            config = PropertyModelConfig()
        
        # Create instance and load weights
        instance = cls(config)
        instance.model = keras.models.load_model(path)
        return instance
    
    def export_tflite(
        self,
        path: str,
        optimize: bool = True,
        representative_dataset: Optional[Callable] = None
    ) -> None:
        """
        Export model to TensorFlow Lite format.
        
        Args:
            path: Output path for .tflite file
            optimize: Whether to apply optimizations
            representative_dataset: Dataset for full integer quantization
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        if optimize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            if representative_dataset is not None:
                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [
                    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
                ]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        with open(path, 'wb') as f:
            f.write(tflite_model)
        
        # Log model size
        size_mb = len(tflite_model) / (1024 * 1024)
        print(f"TFLite model exported: {path}")
        print(f"Model size: {size_mb:.2f} MB")
    
    def get_model_size(self) -> float:
        """Get model size in MB."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.keras', delete=False) as f:
            temp_path = f.name
        
        self.save(temp_path)
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        os.remove(temp_path)
        
        return size_mb
    
    def summary(self) -> None:
        """Print model summary."""
        self.model.summary()
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return self.model.count_params()


def create_property_predictor(
    input_shape: Tuple[int, int, int] = (64, 64, 1),
    **kwargs
) -> PropertyPredictor:
    """Factory function to create a property predictor."""
    config = PropertyModelConfig(input_shape=input_shape, **kwargs)
    return PropertyPredictor(config)
{"input_shape": [64, 64, 1], "object_types": ["hand", "tool", "other"], "grasp_states": ["open", "closed", "pinching"], "interaction_intents": ["pointing", "manipulating", "resting"]}
{"input_shape": [64, 64, 1], "materials": ["rigid", "soft", "liquid"], "size_categories": ["small", "medium", "large"]}

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
"""
Edge Inference Engine for Shadow Intelligence Layer.

Optimized inference for mobile NPUs using TensorFlow Lite.
Supports both intent classification and property prediction.
"""

from __future__ import annotations

import os
import sys
import numpy as np
import tensorflow as tf
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.intent_classifier import IntentPrediction
from models.property_predictor import PropertyPrediction


class InferenceMode(Enum):
    """Inference execution mode."""
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"  # Neural Processing Unit (e.g., Hexagon DSP)
    AUTO = "auto"


@dataclass
class InferenceResult:
    """Result from edge inference."""
    intent: Optional[IntentPrediction]
    properties: Optional[PropertyPrediction]
    inference_time_ms: float
    preprocessing_time_ms: float
    total_time_ms: float


class EdgeInferenceEngine:
    """
    Optimized edge inference engine for shadow intelligence.
    
    Features:
    - TFLite interpreter with delegate support
    - Batch processing for efficiency
    - Input preprocessing pipeline
    - Performance monitoring
    """
    
    def __init__(
        self,
        intent_model_path: Optional[str] = None,
        property_model_path: Optional[str] = None,
        mode: InferenceMode = InferenceMode.AUTO,
        num_threads: int = 4,
        enable_profiling: bool = False
    ) -> None:
        """
        Initialize edge inference engine.
        
        Args:
            intent_model_path: Path to intent classifier TFLite model
            property_model_path: Path to property predictor TFLite model
            mode: Inference execution mode
            num_threads: Number of CPU threads
            enable_profiling: Enable detailed profiling
        """
        self.intent_model_path = intent_model_path
        self.property_model_path = property_model_path
        self.mode = mode
        self.num_threads = num_threads
        self.enable_profiling = enable_profiling
        
        self.intent_interpreter: Optional[tf.lite.Interpreter] = None
        self.property_interpreter: Optional[tf.lite.Interpreter] = None
        
        self._input_shape: Optional[Tuple[int, ...]] = None
        self._preprocessing_pipeline: List[Callable] = []
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load TFLite models with appropriate delegates."""
        # Load intent classifier
        if self.intent_model_path and os.path.exists(self.intent_model_path):
            print(f"Loading intent model: {self.intent_model_path}")
            
            delegates = self._get_delegates()
            
            self.intent_interpreter = tf.lite.Interpreter(
                model_path=self.intent_model_path,
                experimental_delegates=delegates if delegates else None,
                num_threads=self.num_threads
            )
            self.intent_interpreter.allocate_tensors()
            
            # Cache input shape
            input_details = self.intent_interpreter.get_input_details()
            self._input_shape = tuple(input_details[0]['shape'][1:])
            
            print(f"  Input shape: {self._input_shape}")
            print(f"  Delegates: {[d.__class__.__name__ for d in delegates] if delegates else 'None'}")
        
        # Load property predictor
        if self.property_model_path and os.path.exists(self.property_model_path):
            print(f"Loading property model: {self.property_model_path}")
            
            delegates = self._get_delegates()
            
            self.property_interpreter = tf.lite.Interpreter(
                model_path=self.property_model_path,
                experimental_delegates=delegates if delegates else None,
                num_threads=self.num_threads
            )
            self.property_interpreter.allocate_tensors()
            
            if self._input_shape is None:
                input_details = self.property_interpreter.get_input_details()
                self._input_shape = tuple(input_details[0]['shape'][1:])
            
            print(f"  Input shape: {self._input_shape}")
    
    def _get_delegates(self) -> List[tf.lite.experimental.Delegate]:
        """Get appropriate delegates for the execution mode."""
        delegates = []
        
        if self.mode == InferenceMode.GPU:
            try:
                gpu_delegate = tf.lite.experimental.load_delegate('libgpu_delegate.so')
                delegates.append(gpu_delegate)
            except Exception as e:
                print(f"  Warning: GPU delegate not available: {e}")
        
        elif self.mode == InferenceMode.NPU:
            # Try Hexagon delegate for Qualcomm DSP
            try:
                hexagon_delegate = tf.lite.experimental.load_delegate(
                    'libhexagon_delegate.so',
                    {'inference_priority': 'fp16'}
                )
                delegates.append(hexagon_delegate)
            except Exception as e:
                print(f"  Warning: Hexagon delegate not available: {e}")
            
            # Try NNAPI delegate for Android NPU
            try:
                from tensorflow.lite.python.interpreter import load_delegate
                nnapi_delegate = load_delegate('libnnapi_delegate.so')
                delegates.append(nnapi_delegate)
            except Exception as e:
                print(f"  Warning: NNAPI delegate not available: {e}")
        
        elif self.mode == InferenceMode.AUTO:
            # Try all available delegates
            for delegate_name in ['libnnapi_delegate.so', 'libgpu_delegate.so']:
                try:
                    from tensorflow.lite.python.interpreter import load_delegate
                    delegate = load_delegate(delegate_name)
                    delegates.append(delegate)
                    break  # Use first available
                except:
                    continue
        
        return delegates
    
    def preprocess(
        self,
        shadow_data: np.ndarray,
        normalize: bool = True,
        resize: bool = True
    ) -> np.ndarray:
        """
        Preprocess shadow data for inference.
        
        Args:
            shadow_data: Input shadow data (H, W) or (N, H, W)
            normalize: Normalize to [0, 1]
            resize: Resize to model input shape
        
        Returns:
            Preprocessed data ready for inference
        """
        start_time = time.perf_counter()
        
        # Ensure correct shape
        if len(shadow_data.shape) == 2:
            shadow_data = np.expand_dims(shadow_data, axis=0)
        
        # Add channel dimension if needed
        if len(shadow_data.shape) == 3:
            shadow_data = np.expand_dims(shadow_data, axis=-1)
        
        # Resize if needed
        if resize and self._input_shape is not None:
            target_h, target_w = self._input_shape[:2]
            if shadow_data.shape[1:3] != (target_h, target_w):
                shadow_data = tf.image.resize(
                    shadow_data,
                    [target_h, target_w],
                    method='bilinear'
                ).numpy()
        
        # Normalize
        if normalize:
            if shadow_data.max() > 1.0:
                shadow_data = shadow_data / 255.0
            shadow_data = shadow_data.astype(np.float32)
        
        preprocessing_time = (time.perf_counter() - start_time) * 1000
        
        return shadow_data, preprocessing_time
    
    def classify_intent(
        self,
        shadow_data: np.ndarray
    ) -> List[IntentPrediction]:
        """
        Classify intent from shadow data.
        
        Args:
            shadow_data: Preprocessed shadow data
        
        Returns:
            List of IntentPrediction objects
        """
        if self.intent_interpreter is None:
            raise RuntimeError("Intent model not loaded")
        
        # Get interpreter details
        input_details = self.intent_interpreter.get_input_details()
        output_details = self.intent_interpreter.get_output_details()
        
        # Ensure correct dtype
        input_dtype = input_details[0]['dtype']
        if input_dtype == np.int8:
            # Quantized model - convert to int8
            scale, zero_point = input_details[0]['quantization']
            shadow_data = (shadow_data / scale + zero_point).astype(np.int8)
        
        # Run inference
        self.intent_interpreter.set_tensor(input_details[0]['index'], shadow_data)
        self.intent_interpreter.invoke()
        
        # Get outputs
        outputs = []
        for output_detail in output_details:
            output = self.intent_interpreter.get_tensor(output_detail['index'])
            
            # Dequantize if needed
            if output_detail['dtype'] == np.int8:
                scale, zero_point = output_detail['quantization']
                output = (output.astype(np.float32) - zero_point) * scale
            
            outputs.append(output)
        
        # Convert to predictions
        object_pred, grasp_pred, interaction_pred = outputs
        
        predictions = []
        for i in range(len(shadow_data)):
            obj_idx = np.argmax(object_pred[i])
            grasp_idx = np.argmax(grasp_pred[i])
            interaction_idx = np.argmax(interaction_pred[i])
            
            pred = IntentPrediction(
                object_type=["hand", "tool", "other"][obj_idx],
                object_confidence=float(object_pred[i][obj_idx]),
                grasp_state=["open", "closed", "pinching"][grasp_idx],
                grasp_confidence=float(grasp_pred[i][grasp_idx]),
                interaction_intent=["pointing", "manipulating", "resting"][interaction_idx],
                interaction_confidence=float(interaction_pred[i][interaction_idx]),
                overall_confidence=float(
                    object_pred[i][obj_idx] * 
                    grasp_pred[i][grasp_idx] * 
                    interaction_pred[i][interaction_idx]
                ),
                raw_logits={
                    "object_type": object_pred[i],
                    "grasp_state": grasp_pred[i],
                    "interaction_intent": interaction_pred[i]
                }
            )
            predictions.append(pred)
        
        return predictions
    
    def predict_properties(
        self,
        shadow_data: np.ndarray
    ) -> List[PropertyPrediction]:
        """
        Predict properties from shadow data.
        
        Args:
            shadow_data: Preprocessed shadow data
        
        Returns:
            List of PropertyPrediction objects
        """
        if self.property_interpreter is None:
            raise RuntimeError("Property model not loaded")
        
        # Get interpreter details
        input_details = self.property_interpreter.get_input_details()
        output_details = self.property_interpreter.get_output_details()
        
        # Ensure correct dtype
        input_dtype = input_details[0]['dtype']
        if input_dtype == np.int8:
            scale, zero_point = input_details[0]['quantization']
            shadow_data = (shadow_data / scale + zero_point).astype(np.int8)
        
        # Run inference
        self.property_interpreter.set_tensor(input_details[0]['index'], shadow_data)
        self.property_interpreter.invoke()
        
        # Get outputs
        outputs = []
        for output_detail in output_details:
            output = self.property_interpreter.get_tensor(output_detail['index'])
            
            # Dequantize if needed
            if output_detail['dtype'] == np.int8:
                scale, zero_point = output_detail['quantization']
                output = (output.astype(np.float32) - zero_point) * scale
            
            outputs.append(output)
        
        # Convert to predictions
        material_pred, size_pred = outputs
        
        predictions = []
        materials = ["rigid", "soft", "liquid"]
        size_categories = ["small", "medium", "large"]
        
        for i in range(len(shadow_data)):
            mat_idx = np.argmax(material_pred[i])
            size_idx = np.argmax(size_pred[i])
            
            mat_probs = {
                materials[j]: float(material_pred[i][j])
                for j in range(len(materials))
            }
            size_probs = {
                size_categories[j]: float(size_pred[i][j])
                for j in range(len(size_categories))
            }
            
            pred = PropertyPrediction(
                material=materials[mat_idx],
                material_confidence=float(material_pred[i][mat_idx]),
                size_category=size_categories[size_idx],
                size_confidence=float(size_pred[i][size_idx]),
                material_probabilities=mat_probs,
                size_probabilities=size_probs,
                overall_confidence=float(
                    material_pred[i][mat_idx] * size_pred[i][size_idx]
                )
            )
            predictions.append(pred)
        
        return predictions
    
    def infer(
        self,
        shadow_data: np.ndarray,
        run_intent: bool = True,
        run_property: bool = True
    ) -> InferenceResult:
        """
        Run complete inference pipeline.
        
        Args:
            shadow_data: Raw shadow data
            run_intent: Run intent classification
            run_property: Run property prediction
        
        Returns:
            InferenceResult with all predictions
        """
        total_start = time.perf_counter()
        
        # Preprocess
        processed_data, preprocessing_time = self.preprocess(shadow_data)
        
        # Run intent classification
        intent_start = time.perf_counter()
        intent_result = None
        if run_intent and self.intent_interpreter is not None:
            intent_result = self.classify_intent(processed_data)[0]
        intent_time = (time.perf_counter() - intent_start) * 1000
        
        # Run property prediction
        property_start = time.perf_counter()
        property_result = None
        if run_property and self.property_interpreter is not None:
            property_result = self.predict_properties(processed_data)[0]
        property_time = (time.perf_counter() - property_start) * 1000
        
        total_time = (time.perf_counter() - total_start) * 1000
        inference_time = intent_time + property_time
        
        return InferenceResult(
            intent=intent_result,
            properties=property_result,
            inference_time_ms=inference_time,
            preprocessing_time_ms=preprocessing_time,
            total_time_ms=total_time
        )
    
    def benchmark(
        self,
        num_runs: int = 100,
        warmup_runs: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark inference performance.
        
        Args:
            num_runs: Number of benchmark runs
            warmup_runs: Number of warmup runs
        
        Returns:
            Dictionary with benchmark results
        """
        if self._input_shape is None:
            raise RuntimeError("Models not loaded")
        
        # Create dummy input
        dummy_input = np.random.rand(1, *self._input_shape).astype(np.float32)
        
        # Warmup
        print(f"Warming up ({warmup_runs} runs)...")
        for _ in range(warmup_runs):
            self.infer(dummy_input)
        
        # Benchmark
        print(f"Benchmarking ({num_runs} runs)...")
        times = []
        
        for _ in range(num_runs):
            result = self.infer(dummy_input)
            times.append(result.total_time_ms)
        
        results = {
            'mean_ms': np.mean(times),
            'std_ms': np.std(times),
            'min_ms': np.min(times),
            'max_ms': np.max(times),
            'p50_ms': np.percentile(times, 50),
            'p95_ms': np.percentile(times, 95),
            'p99_ms': np.percentile(times, 99),
            'throughput_fps': 1000 / np.mean(times)
        }
        
        print("\nBenchmark Results:")
        print(f"  Mean: {results['mean_ms']:.2f} ms")
        print(f"  Std:  {results['std_ms']:.2f} ms")
        print(f"  Min:  {results['min_ms']:.2f} ms")
        print(f"  Max:  {results['max_ms']:.2f} ms")
        print(f"  P95:  {results['p95_ms']:.2f} ms")
        print(f"  P99:  {results['p99_ms']:.2f} ms")
        print(f"  Throughput: {results['throughput_fps']:.1f} FPS")
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        info = {
            'intent_model_loaded': self.intent_interpreter is not None,
            'property_model_loaded': self.property_interpreter is not None,
            'input_shape': self._input_shape,
            'mode': self.mode.value,
            'num_threads': self.num_threads
        }
        
        if self.intent_interpreter:
            input_details = self.intent_interpreter.get_input_details()
            output_details = self.intent_interpreter.get_output_details()
            
            info['intent_input'] = {
                'shape': input_details[0]['shape'].tolist(),
                'dtype': str(input_details[0]['dtype']),
                'quantization': input_details[0]['quantization']
            }
            info['intent_outputs'] = [
                {
                    'shape': o['shape'].tolist(),
                    'dtype': str(o['dtype']),
                    'quantization': o['quantization']
                }
                for o in output_details
            ]
        
        return info


def create_edge_engine(
    intent_model: Optional[str] = None,
    property_model: Optional[str] = None,
    mode: str = "auto",
    num_threads: int = 4
) -> EdgeInferenceEngine:
    """Factory function to create edge inference engine."""
    inference_mode = InferenceMode(mode)
    return EdgeInferenceEngine(
        intent_model_path=intent_model,
        property_model_path=property_model,
        mode=inference_mode,
        num_threads=num_threads
    )
"""
Edge Inference Engine for Intent Classification
===============================================

Lightweight inference for shadow intent prediction.
Optimized for edge deployment with <5ms latency.

Author: Cognitive AR Empire Technical Team
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# Try to import TensorFlow Lite, fall back to regular TF
try:
    import tflite_runtime.interpreter as tflite
    USE_TFLITE = True
except ImportError:
    import tensorflow as tf
    USE_TFLITE = False


@dataclass
class InferenceConfig:
    """Configuration for edge inference."""
    model_path: str = "models/pretrained/intent_model.tflite"
    n_points: int = 64
    input_dims: int = 3
    num_classes: int = 3
    class_names: Tuple[str, ...] = ('hand', 'tool', 'other')


class EdgeInferenceEngine:
    """
    Edge inference engine for intent classification.
    
    Supports both TFLite (preferred for edge) and regular TensorFlow.
    Optimized for sub-5ms inference on mobile NPUs.
    
    Usage:
        engine = EdgeInferenceEngine()
        result = engine.predict(contour)
        print(result['class'], result['confidence'])
    """
    
    def __init__(self, config: InferenceConfig = None):
        self.config = config or InferenceConfig()
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the TFLite or TensorFlow model."""
        model_path = self.config.model_path
        
        if not model_path.endswith('.tflite'):
            # Try to find TFLite version
            tflite_path = model_path.replace('.keras', '.tflite')
            if tf.io.gfile.exists(tflite_path):
                model_path = tflite_path
        
        if USE_TFLITE and model_path.endswith('.tflite'):
            self._load_tflite(model_path)
        else:
            self._load_tensorflow(model_path)
    
    def _load_tflite(self, model_path: str) -> None:
        """Load TFLite model."""
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Check input shape
        expected_shape = (1, self.config.n_points, self.config.input_dims)
        actual_shape = tuple(self.input_details[0]['shape'])
        
        if actual_shape != expected_shape:
            raise ValueError(
                f"Model input shape {actual_shape} doesn't match "
                f"expected {expected_shape}"
            )
    
    def _load_tensorflow(self, model_path: str) -> None:
        """Load regular TensorFlow model."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from model import IntentClassifier
        
        self.interpreter = IntentClassifier.load(model_path)
        self.input_details = None
        self.output_details = None
    
    def preprocess(self, contour: np.ndarray) -> np.ndarray:
        """
        Preprocess contour for inference.
        
        Args:
            contour: (N, 2+) array of points, may have confidence
            
        Returns:
            (1, 64, 3) normalized array
        """
        # Ensure we have at least 2D points
        if contour.ndim == 1:
            raise ValueError("Contour must be 2D array")
        
        # Resample to fixed number of points
        n_input = len(contour)
        if n_input != self.config.n_points:
            # Linear interpolation
            old_indices = np.linspace(0, n_input - 1, n_input)
            new_indices = np.linspace(0, n_input - 1, self.config.n_points)
            
            resampled = np.zeros((self.config.n_points, contour.shape[1]))
            for dim in range(contour.shape[1]):
                resampled[:, dim] = np.interp(
                    new_indices, old_indices, contour[:, dim]
                )
            contour = resampled
        
        # Add confidence if missing
        if contour.shape[1] == 2:
            confidence = np.ones((len(contour), 1)) * 0.9
            contour = np.concatenate([contour, confidence], axis=1)
        
        # Normalize
        centroid = contour[:, :2].mean(axis=0)
        contour[:, :2] -= centroid
        
        scale = contour[:, :2].std()
        if scale > 0:
            contour[:, :2] /= scale
        
        # Add batch dimension
        return np.expand_dims(contour, axis=0).astype(np.float32)
    
    def predict(self, contour: np.ndarray) -> Dict:
        """
        Predict intent from contour.
        
        Args:
            contour: (N, 2+) contour points
            
        Returns:
            Dictionary with prediction results
        """
        # Preprocess
        input_data = self.preprocess(contour)
        
        # Inference
        if USE_TFLITE and self.input_details is not None:
            # TFLite inference
            self.interpreter.set_tensor(
                self.input_details[0]['index'], input_data
            )
            self.interpreter.invoke()
            predictions = self.interpreter.get_tensor(
                self.output_details[0]['index']
            )
        else:
            # TensorFlow inference
            predictions = self.interpreter.model.predict(input_data, verbose=0)
        
        # Process output
        probs = predictions[0]
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx])
        
        return {
            'class': self.config.class_names[class_idx],
            'class_index': class_idx,
            'confidence': confidence,
            'probabilities': {
                name: float(prob) 
                for name, prob in zip(self.config.class_names, probs)
            },
            'inference_time_ms': None  # Will be set by benchmark
        }
    
    def benchmark(self, n_iterations: int = 100) -> Dict:
        """
        Benchmark inference latency.
        
        Args:
            n_iterations: Number of benchmark iterations
            
        Returns:
            Benchmark results
        """
        # Generate random test contour
        test_contour = np.random.randn(64, 3).astype(np.float32)
        
        # Warm-up
        for _ in range(10):
            self.predict(test_contour)
        
        # Benchmark
        times = []
        for _ in range(n_iterations):
            start = time.perf_counter()
            result = self.predict(test_contour)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        times = np.array(times)
        
        return {
            'mean_ms': float(np.mean(times)),
            'std_ms': float(np.std(times)),
            'min_ms': float(np.min(times)),
            'max_ms': float(np.max(times)),
            'p99_ms': float(np.percentile(times, 99)),
            'iterations': n_iterations
        }


class BatchInferenceEngine:
    """
    Batch inference for processing multiple contours efficiently.
    """
    
    def __init__(self, config: InferenceConfig = None):
        self.config = config or InferenceConfig()
        self.engine = EdgeInferenceEngine(self.config)
    
    def predict_batch(self, contours: List[np.ndarray]) -> List[Dict]:
        """
        Predict intents for multiple contours.
        
        Args:
            contours: List of contour arrays
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        for contour in contours:
            result = self.engine.predict(contour)
            results.append(result)
        return results
    
    def benchmark_batch(
        self, 
        batch_sizes: List[int] = [1, 5, 10, 20],
        n_iterations: int = 50
    ) -> Dict:
        """
        Benchmark batch inference performance.
        
        Args:
            batch_sizes: List of batch sizes to test
            n_iterations: Iterations per batch size
            
        Returns:
            Benchmark results by batch size
        """
        results = {}
        
        for batch_size in batch_sizes:
            # Generate test batch
            test_contours = [
                np.random.randn(64, 3).astype(np.float32)
                for _ in range(batch_size)
            ]
            
            # Warm-up
            self.predict_batch(test_contours)
            
            # Benchmark
            times = []
            for _ in range(n_iterations):
                start = time.perf_counter()
                self.predict_batch(test_contours)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            
            times = np.array(times)
            results[batch_size] = {
                'total_ms': float(np.mean(times)),
                'per_item_ms': float(np.mean(times) / batch_size),
                'std_ms': float(np.std(times)),
                'p99_ms': float(np.percentile(times, 99))
            }
        
        return results


def create_inference_engine(
    model_path: str = None,
    use_tflite: bool = True
) -> EdgeInferenceEngine:
    """
    Factory function to create inference engine.
    
    Args:
        model_path: Path to model file
        use_tflite: Prefer TFLite if available
        
    Returns:
        Configured EdgeInferenceEngine
    """
    if model_path is None:
        model_path = "models/pretrained/intent_model.tflite"
    
    config = InferenceConfig(model_path=model_path)
    return EdgeInferenceEngine(config)


def main():
    """Demo inference engine."""
    print("=" * 60)
    print("EDGE INFERENCE ENGINE DEMO")
    print("=" * 60)
    
    # Create engine
    print("\n[1] Creating inference engine...")
    engine = create_inference_engine()
    print(f"    Using: {'TFLite' if USE_TFLITE else 'TensorFlow'}")
    
    # Generate test contour (hand-like)
    print("\n[2] Generating test contour...")
    t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    x = 0.05 * np.cos(t) + 0.01 * np.sin(5 * t)
    y = 0.06 * np.sin(t) + 0.005 * np.cos(7 * t)
    confidence = 0.8 + 0.2 * np.random.random(64)
    test_contour = np.column_stack([x, y, confidence])
    
    # Predict
    print("\n[3] Running prediction...")
    result = engine.predict(test_contour)
    
    print(f"    Predicted class: {result['class']}")
    print(f"    Confidence: {result['confidence']:.3f}")
    print("    All probabilities:")
    for name, prob in result['probabilities'].items():
        print(f"      {name}: {prob:.3f}")
    
    # Benchmark
    print("\n[4] Running benchmark (100 iterations)...")
    bench = engine.benchmark(n_iterations=100)
    
    print(f"    Mean latency: {bench['mean_ms']:.3f} ms")
    print(f"    P99 latency: {bench['p99_ms']:.3f} ms")
    print(f"    Min/Max: {bench['min_ms']:.3f} / {bench['max_ms']:.3f} ms")
    
    # Check target
    if bench['p99_ms'] < 5.0:
        print("\n✅ TARGET MET: P99 < 5ms")
    else:
        print(f"\n⚠️  TARGET NOT MET: P99 = {bench['p99_ms']:.2f}ms")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
"""
Smartphone Integration Example for Shadow Intelligence Layer.

Demonstrates how to integrate the intelligence layer into a mobile application.
Includes examples for Android (Kotlin) and iOS (Swift) integration.
"""

from __future__ import annotations

import os
import sys
import numpy as np
from typing import Dict, List, Optional, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.intelligence_api import IntelligenceAPI, ShadowIntelligence, classify


class SmartphoneIntegration:
    """
    Example integration for smartphone applications.
    
    This class demonstrates best practices for integrating the
    Shadow Intelligence Layer into mobile apps.
    """
    
    def __init__(
        self,
        models_dir: str = "models/pretrained",
        use_npu: bool = True
    ) -> None:
        """
        Initialize smartphone integration.
        
        Args:
            models_dir: Directory containing TFLite models
            use_npu: Whether to use NPU acceleration if available
        """
        self.models_dir = models_dir
        self.use_npu = use_npu
        
        # Initialize API
        mode = "npu" if use_npu else "auto"
        self.api = IntelligenceAPI(
            intent_model_path=os.path.join(models_dir, "intent_model.tflite"),
            property_model_path=os.path.join(models_dir, "property_model.tflite"),
            mode=mode,
            num_threads=4
        )
        
        # Performance tracking
        self.frame_count = 0
        self.total_latency = 0.0
    
    def process_shadow_frame(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Process a single shadow frame from camera.
        
        Args:
            shadow_data: Shadow observation (64x64 grayscale)
        
        Returns:
            Dictionary with classification results
        """
        # Run classification
        result = self.api.classify(shadow_data)
        
        # Update stats
        self.frame_count += 1
        self.total_latency += result.inference_time_ms
        
        # Format output for mobile app
        return self._format_result(result)
    
    def _format_result(self, result: ShadowIntelligence) -> Dict[str, Any]:
        """Format result for mobile app consumption."""
        output = {
            "object": {
                "type": result.object_type,
                "confidence": round(result.object_confidence, 3)
            },
            "properties": {
                "material": result.material,
                "material_confidence": round(result.material_confidence, 3),
                "size": result.size_category,
                "size_confidence": round(result.size_confidence, 3)
            },
            "overall_confidence": round(result.overall_confidence, 3),
            "inference_time_ms": round(result.inference_time_ms, 2)
        }
        
        # Add hand-specific info
        if result.is_hand():
            output["hand"] = {
                "grasp_state": result.grasp_state,
                "grasp_confidence": round(result.grasp_confidence, 3) if result.grasp_confidence else None,
                "interaction_intent": result.interaction_intent,
                "interaction_confidence": round(result.interaction_confidence, 3) if result.interaction_confidence else None
            }
        
        return output
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if self.frame_count == 0:
            return {"frames_processed": 0, "average_latency_ms": 0}
        
        return {
            "frames_processed": self.frame_count,
            "average_latency_ms": round(self.total_latency / self.frame_count, 2),
            "current_fps": round(1000 / (self.total_latency / self.frame_count), 1)
        }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.frame_count = 0
        self.total_latency = 0.0


# Android (Kotlin) Integration Example
ANDROID_KOTLIN_EXAMPLE = '''
// Android Integration Example - Kotlin
// Add to your app's build.gradle:
// implementation 'org.tensorflow:tensorflow-lite:2.14.0'
// implementation 'org.tensorflow:tensorflow-lite-gpu:2.14.0'
// implementation 'org.tensorflow:tensorflow-lite-nnapi:2.14.0'

package com.example.shadowintelligence

import android.content.Context
import android.graphics.Bitmap
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.GpuDelegate
import org.tensorflow.lite.nnapi.NnApiDelegate
import java.nio.ByteBuffer
import java.nio.ByteOrder

class ShadowIntelligenceModel(context: Context) {
    
    private var interpreter: Interpreter? = null
    private val inputSize = 64
    private val numChannels = 1
    
    init {
        // Load model with NPU/GPU acceleration
        val options = Interpreter.Options().apply {
            // Try NNAPI (NPU) first
            addDelegate(NnApiDelegate())
            // Fallback to GPU
            // addDelegate(GpuDelegate())
            setNumThreads(4)
        }
        
        val model = context.assets.open("intent_model.tflite").readBytes()
        interpreter = Interpreter(model, options)
    }
    
    fun classify(shadowBitmap: Bitmap): IntelligenceResult {
        // Preprocess bitmap to input buffer
        val inputBuffer = ByteBuffer.allocateDirect(
            4 * inputSize * inputSize * numChannels
        ).order(ByteOrder.nativeOrder())
        
        // Convert bitmap to grayscale and normalize
        for (y in 0 until inputSize) {
            for (x in 0 until inputSize) {
                val pixel = shadowBitmap.getPixel(x, y)
                val gray = (0.299 * (pixel shr 16 and 0xFF) +
                           0.587 * (pixel shr 8 and 0xFF) +
                           0.114 * (pixel and 0xFF)) / 255.0f
                inputBuffer.putFloat(gray)
            }
        }
        
        // Run inference
        val objectOutput = Array(1) { FloatArray(3) }
        val graspOutput = Array(1) { FloatArray(3) }
        val interactionOutput = Array(1) { FloatArray(3) }
        
        interpreter?.runForMultipleInputsOutputs(
            arrayOf(inputBuffer),
            mapOf(
                0 to objectOutput,
                1 to graspOutput,
                2 to interactionOutput
            )
        )
        
        // Parse results
        return IntelligenceResult(
            objectType = argMax(objectOutput[0]),
            objectConfidence = objectOutput[0].max()!!,
            graspState = argMax(graspOutput[0]),
            graspConfidence = graspOutput[0].max()!!,
            interactionIntent = argMax(interactionOutput[0]),
            interactionConfidence = interactionOutput[0].max()!!
        )
    }
    
    private fun argMax(array: FloatArray): String {
        val labels = arrayOf("hand", "tool", "other")
        return labels[array.indices.maxBy { array[it] } ?: 0]
    }
    
    fun close() {
        interpreter?.close()
    }
}

data class IntelligenceResult(
    val objectType: String,
    val objectConfidence: Float,
    val graspState: String,
    val graspConfidence: Float,
    val interactionIntent: String,
    val interactionConfidence: Float
)
'''


# iOS (Swift) Integration Example
IOS_SWIFT_EXAMPLE = '''
// iOS Integration Example - Swift
// Add to Podfile:
// pod 'TensorFlowLiteSwift'

import TensorFlowLite
import CoreImage

class ShadowIntelligenceModel {
    
    private var interpreter: Interpreter?
    private let inputSize = 64
    
    init?() {
        // Load model
        guard let modelPath = Bundle.main.path(
            forResource: "intent_model",
            ofType: "tflite"
        ) else {
            return nil
        }
        
        // Configure with Core ML delegate for NPU
        var options = Interpreter.Options()
        options.threadCount = 4
        
        // Use Core ML delegate for Apple Neural Engine
        let coreMLOptions = CoreMLDelegate.Options(
            enabledDevices: .neuralEngine
        )
        let coreMLDelegate = CoreMLDelegate(options: coreMLOptions)
        
        do {
            interpreter = try Interpreter(
                modelPath: modelPath,
                options: options,
                delegates: [coreMLDelegate]
            )
            try interpreter?.allocateTensors()
        } catch {
            print("Failed to create interpreter: \\(error)")
            return nil
        }
    }
    
    func classify(shadowImage: CIImage) -> IntelligenceResult? {
        // Resize and convert to grayscale
        guard let resized = resizeImage(shadowImage, to: CGSize(
            width: inputSize,
            height: inputSize
        )) else {
            return nil
        }
        
        // Convert to input data
        guard let inputData = imageToInputData(resized) else {
            return nil
        }
        
        // Run inference
        do {
            try interpreter?.copy(inputData, toInputAt: 0)
            try interpreter?.invoke()
            
            // Get outputs
            let objectOutput = try interpreter!.output(at: 0)
            let graspOutput = try interpreter!.output(at: 1)
            let interactionOutput = try interpreter!.output(at: 2)
            
            // Parse results
            let objectData = objectOutput.data.toArray(type: Float.self)
            let graspData = graspOutput.data.toArray(type: Float.self)
            let interactionData = interactionOutput.data.toArray(type: Float.self)
            
            return IntelligenceResult(
                objectType: argMax(objectData),
                objectConfidence: objectData.max() ?? 0,
                graspState: argMax(graspData),
                graspConfidence: graspData.max() ?? 0,
                interactionIntent: argMax(interactionData),
                interactionConfidence: interactionData.max() ?? 0
            )
        } catch {
            print("Inference failed: \\(error)")
            return nil
        }
    }
    
    private func argMax(_ array: [Float]) -> String {
        let labels = ["hand", "tool", "other"]
        guard let maxIndex = array.enumerated().max(by: { $0.element < $1.element })?.offset else {
            return labels[0]
        }
        return labels[maxIndex]
    }
    
    private func resizeImage(_ image: CIImage, to size: CGSize) -> CIImage? {
        let scaleX = size.width / image.extent.width
        let scaleY = size.height / image.extent.height
        return image.transformed(by: CGAffineTransform(scaleX: scaleX, y: scaleY))
    }
    
    private func imageToInputData(_ image: CIImage) -> Data? {
        // Convert CIImage to grayscale float array
        let context = CIContext()
        guard let cgImage = context.createCGImage(image, from: image.extent) else {
            return nil
        }
        
        let width = cgImage.width
        let height = cgImage.height
        let bytesPerPixel = 4
        let bytesPerRow = bytesPerPixel * width
        let bitsPerComponent = 8
        
        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        
        guard let context = CGContext(
            data: &pixels,
            width: width,
            height: height,
            bitsPerComponent: bitsPerComponent,
            bytesPerRow: bytesPerRow,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return nil
        }
        
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        
        // Convert to grayscale floats
        var floatData = [Float]()
        for y in 0..<height {
            for x in 0..<width {
                let offset = (y * width + x) * 4
                let r = Float(pixels[offset])
                let g = Float(pixels[offset + 1])
                let b = Float(pixels[offset + 2])
                let gray = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                floatData.append(gray)
            }
        }
        
        return floatData.withUnsafeBufferPointer { Data(buffer: $0) }
    }
}

struct IntelligenceResult {
    let objectType: String
    let objectConfidence: Float
    let graspState: String
    let graspConfidence: Float
    let interactionIntent: String
    let interactionConfidence: Float
}

extension Data {
    func toArray<T>(type: T.Type) -> [T] {
        return self.withUnsafeBytes {
            Array($0.bindMemory(to: T.self))
        }
    }
}
'''


# React Native Integration Example
REACT_NATIVE_EXAMPLE = '''
// React Native Integration Example
// Install: npm install react-native-tensorflow-lite

import * as tf from '@tensorflow/tf-react-native';

class ShadowIntelligenceService {
    constructor() {
        this.intentModel = null;
        this.propertyModel = null;
        this.inputSize = 64;
    }
    
    async initialize() {
        // Load models
        this.intentModel = await tf.loadGraphModel(
            'models/intent_model.tflite'
        );
        this.propertyModel = await tf.loadGraphModel(
            'models/property_model.tflite'
        );
    }
    
    async classify(shadowImageData) {
        // Preprocess image
        const input = tf.tidy(() => {
            const image = tf.browser.fromPixels(shadowImageData, 1);
            const resized = tf.image.resizeBilinear(image, [64, 64]);
            const normalized = resized.div(255.0);
            return normalized.expandDims(0);
        });
        
        // Run inference
        const [objectPred, graspPred, interactionPred] = 
            await this.intentModel.predict(input);
        
        // Parse results
        const objectType = this.argMax(await objectPred.data());
        const graspState = this.argMax(await graspPred.data());
        const interactionIntent = this.argMax(await interactionPred.data());
        
        // Cleanup
        input.dispose();
        objectPred.dispose();
        graspPred.dispose();
        interactionPred.dispose();
        
        return {
            objectType,
            graspState,
            interactionIntent
        };
    }
    
    argMax(array) {
        const labels = ['hand', 'tool', 'other'];
        let maxIndex = 0;
        let maxValue = array[0];
        for (let i = 1; i < array.length; i++) {
            if (array[i] > maxValue) {
                maxValue = array[i];
                maxIndex = i;
            }
        }
        return labels[maxIndex];
    }
}

export default new ShadowIntelligenceService();
'''


def print_integration_examples():
    """Print all integration examples."""
    print("="*70)
    print("SMARTPHONE INTEGRATION EXAMPLES")
    print("="*70)
    
    print("\n" + "="*70)
    print("ANDROID (KOTLIN)")
    print("="*70)
    print(ANDROID_KOTLIN_EXAMPLE)
    
    print("\n" + "="*70)
    print("iOS (SWIFT)")
    print("="*70)
    print(IOS_SWIFT_EXAMPLE)
    
    print("\n" + "="*70)
    print("REACT NATIVE")
    print("="*70)
    print(REACT_NATIVE_EXAMPLE)


def demo_integration():
    """Demonstrate smartphone integration."""
    print("\n" + "="*70)
    print("DEMONSTRATING SMARTPHONE INTEGRATION")
    print("="*70)
    
    # Create integration instance
    integration = SmartphoneIntegration(
        models_dir="../models/pretrained",
        use_npu=False  # Use CPU for demo
    )
    
    # Simulate processing frames
    print("\nSimulating 10 shadow frames...")
    
    for i in range(10):
        # Generate dummy shadow frame
        shadow_frame = np.random.rand(64, 64).astype(np.float32)
        
        # Process frame
        result = integration.process_shadow_frame(shadow_frame)
        
        print(f"\nFrame {i+1}:")
        print(f"  Object: {result['object']['type']} ({result['object']['confidence']:.1%})")
        print(f"  Material: {result['properties']['material']}")
        print(f"  Size: {result['properties']['size']}")
        print(f"  Latency: {result['inference_time_ms']:.2f} ms")
    
    # Print performance stats
    stats = integration.get_performance_stats()
    print("\n" + "-"*40)
    print("Performance Statistics:")
    print(f"  Frames processed: {stats['frames_processed']}")
    print(f"  Average latency: {stats['average_latency_ms']:.2f} ms")
    print(f"  Effective FPS: {stats['current_fps']:.1f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        print_integration_examples()
    else:
        demo_integration()
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
"""
Intelligence API for Shadow Intelligence Layer.

Simple, clean API for intent classification and property prediction.
Designed for easy integration with mobile applications.
"""

from __future__ import annotations

import os
import sys
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference.edge_inference import EdgeInferenceEngine, InferenceMode
from models.intent_classifier import IntentPrediction
from models.property_predictor import PropertyPrediction


class ObjectType(Enum):
    """Object type classification."""
    HAND = "hand"
    TOOL = "tool"
    OTHER = "other"


class GraspState(Enum):
    """Hand grasp state."""
    OPEN = "open"
    CLOSED = "closed"
    PINCHING = "pinching"


class InteractionIntent(Enum):
    """Interaction intent."""
    POINTING = "pointing"
    MANIPULATING = "manipulating"
    RESTING = "resting"


class MaterialType(Enum):
    """Material type."""
    RIGID = "rigid"
    SOFT = "soft"
    LIQUID = "liquid"


class SizeCategory(Enum):
    """Size category."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class ShadowIntelligence:
    """
    Complete intelligence result for a shadow observation.
    
    This is the main output format of the intelligence API.
    """
    # Object classification
    object_type: str
    object_confidence: float
    
    # Intent (if object is a hand)
    grasp_state: Optional[str]
    grasp_confidence: Optional[float]
    interaction_intent: Optional[str]
    interaction_confidence: Optional[float]
    
    # Properties
    material: str
    material_confidence: float
    size_category: str
    size_confidence: float
    
    # Overall
    overall_confidence: float
    
    # Performance metrics
    inference_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def is_hand(self) -> bool:
        """Check if detected object is a hand."""
        return self.object_type == "hand"
    
    def is_tool(self) -> bool:
        """Check if detected object is a tool."""
        return self.object_type == "tool"
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        """Check if prediction meets confidence threshold."""
        return self.overall_confidence >= threshold


class IntelligenceAPI:
    """
    Main API for Shadow Intelligence Layer.
    
    Provides a simple interface for:
    - Intent classification
    - Property prediction
    - Batch processing
    - Performance monitoring
    
    Example:
        >>> api = IntelligenceAPI()
        >>> result = api.classify(shadow_data)
        >>> print(f"Detected: {result.object_type}")
    """
    
    def __init__(
        self,
        intent_model_path: Optional[str] = None,
        property_model_path: Optional[str] = None,
        mode: str = "auto",
        num_threads: int = 4
    ) -> None:
        """
        Initialize Intelligence API.
        
        Args:
            intent_model_path: Path to intent classifier TFLite model
            property_model_path: Path to property predictor TFLite model
            mode: Execution mode ('cpu', 'gpu', 'npu', 'auto')
            num_threads: Number of CPU threads for inference
        """
        # Set default model paths
        if intent_model_path is None:
            intent_model_path = self._find_default_model("intent_model.tflite")
        
        if property_model_path is None:
            property_model_path = self._find_default_model("property_model.tflite")
        
        self.intent_model_path = intent_model_path
        self.property_model_path = property_model_path
        
        # Initialize inference engine
        self.engine = EdgeInferenceEngine(
            intent_model_path=intent_model_path,
            property_model_path=property_model_path,
            mode=InferenceMode(mode),
            num_threads=num_threads
        )
        
        # Performance tracking
        self._inference_count = 0
        self._total_inference_time = 0.0
    
    def _find_default_model(self, model_name: str) -> Optional[str]:
        """Find default model in common locations."""
        search_paths = [
            os.path.join("models", "pretrained", model_name),
            os.path.join("..", "models", "pretrained", model_name),
            os.path.join(os.path.dirname(__file__), "..", "models", "pretrained", model_name),
            model_name
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def classify(
        self,
        shadow_data: np.ndarray,
        return_properties: bool = True
    ) -> ShadowIntelligence:
        """
        Classify shadow data and return intelligence result.
        
        Args:
            shadow_data: Shadow observation data (H, W) or (H, W, 1)
            return_properties: Also predict properties
        
        Returns:
            ShadowIntelligence result object
        """
        # Run inference
        result = self.engine.infer(
            shadow_data,
            run_intent=True,
            run_property=return_properties
        )
        
        # Update performance tracking
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        # Build result
        intent = result.intent
        props = result.properties
        
        # Calculate overall confidence
        if intent and props:
            overall_conf = (intent.overall_confidence + props.overall_confidence) / 2
        elif intent:
            overall_conf = intent.overall_confidence
        elif props:
            overall_conf = props.overall_confidence
        else:
            overall_conf = 0.0
        
        return ShadowIntelligence(
            object_type=intent.object_type if intent else "unknown",
            object_confidence=intent.object_confidence if intent else 0.0,
            grasp_state=intent.grasp_state if intent and intent.object_type == "hand" else None,
            grasp_confidence=intent.grasp_confidence if intent and intent.object_type == "hand" else None,
            interaction_intent=intent.interaction_intent if intent and intent.object_type == "hand" else None,
            interaction_confidence=intent.interaction_confidence if intent and intent.object_type == "hand" else None,
            material=props.material if props else "unknown",
            material_confidence=props.material_confidence if props else 0.0,
            size_category=props.size_category if props else "unknown",
            size_confidence=props.size_confidence if props else 0.0,
            overall_confidence=overall_conf,
            inference_time_ms=result.total_time_ms
        )
    
    def classify_batch(
        self,
        shadow_data_batch: np.ndarray,
        return_properties: bool = True
    ) -> List[ShadowIntelligence]:
        """
        Classify a batch of shadow observations.
        
        Args:
            shadow_data_batch: Batch of shadow data (N, H, W) or (N, H, W, 1)
            return_properties: Also predict properties
        
        Returns:
            List of ShadowIntelligence results
        """
        results = []
        
        # Process each sample
        for i in range(len(shadow_data_batch)):
            result = self.classify(shadow_data_batch[i], return_properties)
            results.append(result)
        
        return results
    
    def get_intent(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get only intent classification (faster, lighter).
        
        Args:
            shadow_data: Shadow observation data
        
        Returns:
            Dictionary with intent information
        """
        result = self.engine.infer(
            shadow_data,
            run_intent=True,
            run_property=False
        )
        
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        intent = result.intent
        
        if intent is None:
            return {"error": "Intent classification failed"}
        
        return {
            "object_type": intent.object_type,
            "object_confidence": intent.object_confidence,
            "grasp_state": intent.grasp_state,
            "grasp_confidence": intent.grasp_confidence,
            "interaction_intent": intent.interaction_intent,
            "interaction_confidence": intent.interaction_confidence,
            "inference_time_ms": result.total_time_ms
        }
    
    def get_properties(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get only property prediction (faster, lighter).
        
        Args:
            shadow_data: Shadow observation data
        
        Returns:
            Dictionary with property information
        """
        result = self.engine.infer(
            shadow_data,
            run_intent=False,
            run_property=True
        )
        
        self._inference_count += 1
        self._total_inference_time += result.total_time_ms
        
        props = result.properties
        
        if props is None:
            return {"error": "Property prediction failed"}
        
        return {
            "material": props.material,
            "material_confidence": props.material_confidence,
            "material_probabilities": props.material_probabilities,
            "size_category": props.size_category,
            "size_confidence": props.size_confidence,
            "size_probabilities": props.size_probabilities,
            "inference_time_ms": result.total_time_ms
        }
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if self._inference_count == 0:
            return {
                "inference_count": 0,
                "average_inference_time_ms": 0.0,
                "total_inference_time_ms": 0.0
            }
        
        return {
            "inference_count": self._inference_count,
            "average_inference_time_ms": self._total_inference_time / self._inference_count,
            "total_inference_time_ms": self._total_inference_time
        }
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics."""
        self._inference_count = 0
        self._total_inference_time = 0.0
    
    def benchmark(self, num_runs: int = 100) -> Dict[str, float]:
        """
        Run performance benchmark.
        
        Args:
            num_runs: Number of benchmark iterations
        
        Returns:
            Benchmark results
        """
        return self.engine.benchmark(num_runs=num_runs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return self.engine.get_model_info()


# Simple function interface for quick usage
def classify(
    shadow_data: np.ndarray,
    intent_model: Optional[str] = None,
    property_model: Optional[str] = None
) -> ShadowIntelligence:
    """
    Simple classification function.
    
    Args:
        shadow_data: Shadow observation data
        intent_model: Path to intent model (optional)
        property_model: Path to property model (optional)
    
    Returns:
        ShadowIntelligence result
    """
    api = IntelligenceAPI(
        intent_model_path=intent_model,
        property_model_path=property_model
    )
    return api.classify(shadow_data)


def quick_classify(shadow_data: np.ndarray) -> Dict[str, str]:
    """
    Ultra-simple classification returning basic info.
    
    Args:
        shadow_data: Shadow observation data
    
    Returns:
        Simple dictionary with key results
    """
    result = classify(shadow_data)
    
    return {
        "object": result.object_type,
        "confidence": f"{result.overall_confidence:.2%}",
        "material": result.material,
        "size": result.size_category
    }


# Flask/FastAPI integration helpers
def create_api_response(result: ShadowIntelligence) -> Dict[str, Any]:
    """Create API response from intelligence result."""
    return {
        "success": True,
        "data": result.to_dict()
    }


def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create error API response."""
    return {
        "success": False,
        "error": error_message
    }


# Example usage
if __name__ == "__main__":
    # Create dummy shadow data for testing
    dummy_shadow = np.random.rand(64, 64).astype(np.float32)
    
    # Initialize API
    api = IntelligenceAPI()
    
    # Run classification
    result = api.classify(dummy_shadow)
    
    # Print results
    print("Classification Result:")
    print(f"  Object Type: {result.object_type} ({result.object_confidence:.2%})")
    
    if result.is_hand():
        print(f"  Grasp State: {result.grasp_state} ({result.grasp_confidence:.2%})")
        print(f"  Interaction: {result.interaction_intent} ({result.interaction_confidence:.2%})")
    
    print(f"  Material: {result.material} ({result.material_confidence:.2%})")
    print(f"  Size: {result.size_category} ({result.size_confidence:.2%})")
    print(f"  Overall Confidence: {result.overall_confidence:.2%}")
    print(f"  Inference Time: {result.inference_time_ms:.2f} ms")
