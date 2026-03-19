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
