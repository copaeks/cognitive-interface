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
