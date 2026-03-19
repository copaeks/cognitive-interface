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
