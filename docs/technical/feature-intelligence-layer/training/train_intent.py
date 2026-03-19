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
