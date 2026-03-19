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
