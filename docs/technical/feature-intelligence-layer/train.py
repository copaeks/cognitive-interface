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
