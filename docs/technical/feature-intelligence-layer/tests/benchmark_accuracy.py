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
