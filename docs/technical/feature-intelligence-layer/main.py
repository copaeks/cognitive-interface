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
