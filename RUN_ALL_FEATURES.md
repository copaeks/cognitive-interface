#!/usr/bin/env python3
"""
Shadow Principle Platform - Feature Demonstration Script
========================================================

This script demonstrates all 5 production-grade features:
1. Universal Shadow Engine (Plugin Architecture)
2. Shadow Mesh 3D (3D Reconstruction + Physics)
3. Distributed Shadow Network (Multi-Array Coordination)
4. HAL + Sim-to-Real Bridge (Hardware Abstraction)
5. Intelligence Layer (Edge AI Intent Classification)

Usage:
    python run_all_features.py [--benchmark] [--visualize]

Author: Cognitive AR Empire Technical Team
Version: 2.0 (Steroids Edition)
"""

import numpy as np
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add feature branches to path
sys.path.insert(0, str(Path(__file__).parent / "feature-universal-engine"))
sys.path.insert(0, str(Path(__file__).parent / "feature-shadow-mesh-3d"))
sys.path.insert(0, str(Path(__file__).parent / "feature-distributed-network"))
sys.path.insert(0, str(Path(__file__).parent / "feature-hal-sim2real"))
sys.path.insert(0, str(Path(__file__).parent / "feature-intelligence-layer"))


class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{'='*70}{Colors.END}\n")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.CYAN}▶ {title}{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")


def print_result(label: str, value: str, status: str = "info"):
    """Print formatted result."""
    color = Colors.GREEN if status == "pass" else Colors.YELLOW if status == "warn" else Colors.BLUE
    print(f"  {label:<30} {color}{value}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


class FeatureDemo:
    """Demonstrates all 5 feature branches."""
    
    def __init__(self, run_benchmarks: bool = True, visualize: bool = False):
        self.run_benchmarks = run_benchmarks
        self.visualize = visualize
        self.results = {}
    
    def demo_universal_engine(self) -> Dict:
        """
        Feature 1: Universal Shadow Engine
        
        Demonstrates plugin-based architecture with acoustic plugin.
        """
        print_header("FEATURE 1: UNIVERSAL SHADOW ENGINE")
        
        try:
            from core.engine import ShadowEngineCore, PluginRegistry
            from plugins.acoustic.plugin import AcousticPlugin, AcousticConfig
            
            print_section("Plugin Registration")
            
            # Initialize engine
            engine = ShadowEngineCore()
            print_result("Engine created", "✓", "pass")
            
            # Register acoustic plugin
            registry = PluginRegistry()
            registry.register("acoustic", AcousticPlugin)
            print_result("Acoustic plugin registered", "✓", "pass")
            
            # Load plugin
            config = AcousticConfig()
            plugin = engine.load_plugin("acoustic", config=config)
            print_result("Plugin loaded", f"v{plugin.version}", "pass")
            
            print_section("Processing Pipeline")
            
            # Generate test signals
            sample_rate = 96000
            duration = 0.01
            n_samples = int(sample_rate * duration)
            
            # Simulate 4-microphone input
            signals = np.random.randn(4, n_samples).astype(np.float32) * 0.1
            
            # Process
            start = time.perf_counter()
            result = engine.process(signals)
            elapsed = (time.perf_counter() - start) * 1000
            
            print_result("Input channels", "4 microphones", "info")
            print_result("Processing time", f"{elapsed:.2f} ms", "pass" if elapsed < 10 else "warn")
            print_result("Output contours", str(len(result.contours)), "info")
            
            if self.run_benchmarks:
                print_section("Benchmarks")
                
                # Plugin registration benchmark
                times = []
                for _ in range(100):
                    start = time.perf_counter()
                    registry.register("test", AcousticPlugin)
                    elapsed = (time.perf_counter() - start) * 1e6
                    times.append(elapsed)
                
                reg_time = np.mean(times)
                print_result("Plugin registration", f"{reg_time:.1f} μs", "pass" if reg_time < 100 else "warn")
            
            self.results['universal_engine'] = {
                'status': 'PASS',
                'latency_ms': elapsed,
                'plugin_version': plugin.version
            }
            
            print_success("Universal Shadow Engine demo complete")
            return self.results['universal_engine']
            
        except Exception as e:
            print_error(f"Universal Engine failed: {e}")
            self.results['universal_engine'] = {'status': 'FAIL', 'error': str(e)}
            return self.results['universal_engine']
    
    def demo_shadow_mesh_3d(self) -> Dict:
        """
        Feature 2: Shadow Mesh 3D
        
        Demonstrates 3D mesh reconstruction with physics inference.
        """
        print_header("FEATURE 2: SHADOW MESH 3D")
        
        try:
            from mesh_generator import MeshGenerator, MeshConfig
            from physics_inference import PhysicsInferenceEngine
            from exporters.obj_exporter import OBJExporter
            
            print_section("3D Mesh Generation")
            
            # Create generator
            config = MeshConfig()
            generator = MeshGenerator(config)
            
            # Generate synthetic 2D contour
            t = np.linspace(0, 2*np.pi, 64, endpoint=False)
            x = 0.05 * np.cos(t) + 0.005 * np.sin(5*t)
            y = 0.06 * np.sin(t) + 0.003 * np.cos(7*t)
            contour_2d = np.column_stack([x, y])
            
            print_result("Input points", str(len(contour_2d)), "info")
            
            # Generate 3D mesh
            start = time.perf_counter()
            mesh = generator.generate_from_contour(contour_2d, method='extrusion')
            elapsed = (time.perf_counter() - start) * 1000
            
            print_result("Vertices", str(len(mesh.vertices)), "info")
            print_result("Faces", str(len(mesh.faces)), "info")
            print_result("Generation time", f"{elapsed:.2f} ms", "pass" if elapsed < 15 else "warn")
            
            print_section("Physics Inference")
            
            # Infer physics properties
            physics = PhysicsInferenceEngine()
            props = physics.infer_all(mesh)
            
            print_result("Material type", props['material_type'], "info")
            print_result("Rigidity", f"{props['rigidity']:.2f}", "info")
            print_result("Density", f"{props['density']:.1f} kg/m³", "info")
            print_result("Mass", f"{props['mass']:.3f} kg", "info")
            
            print_section("Export")
            
            # Export to OBJ
            exporter = OBJExporter()
            obj_data = exporter.export(mesh, props)
            
            print_result("OBJ size", f"{len(obj_data)} bytes", "info")
            print_result("Export format", "Wavefront OBJ", "pass")
            
            if self.run_benchmarks:
                print_section("Benchmarks")
                
                times = []
                for _ in range(100):
                    start = time.perf_counter()
                    mesh = generator.generate_from_contour(contour_2d, method='extrusion')
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                
                mean_time = np.mean(times)
                print_result("Mean mesh generation", f"{mean_time:.2f} ms", "pass" if mean_time < 15 else "warn")
            
            self.results['shadow_mesh_3d'] = {
                'status': 'PASS',
                'vertices': len(mesh.vertices),
                'faces': len(mesh.faces),
                'generation_ms': elapsed,
                'material': props['material_type']
            }
            
            print_success("Shadow Mesh 3D demo complete")
            return self.results['shadow_mesh_3d']
            
        except Exception as e:
            print_error(f"Shadow Mesh 3D failed: {e}")
            self.results['shadow_mesh_3d'] = {'status': 'FAIL', 'error': str(e)}
            return self.results['shadow_mesh_3d']
    
    def demo_distributed_network(self) -> Dict:
        """
        Feature 3: Distributed Shadow Network
        
        Demonstrates multi-array coordination.
        """
        print_header("FEATURE 3: DISTRIBUTED SHADOW NETWORK")
        
        try:
            from network.ptp_sync import PTPSynchronizer
            from fusion.shadow_fusion import ShadowFusionEngine
            from fusion.global_map import GlobalShadowMap
            
            print_section("Time Synchronization")
            
            # Create PTP synchronizer
            ptp = PTPSynchronizer()
            ptp.start()
            
            # Simulate sync
            offset = ptp.get_clock_offset()
            print_result("Clock offset", f"{offset*1e6:.2f} μs", "pass" if abs(offset) < 1e-6 else "warn")
            print_result("Sync status", ptp.get_sync_status(), "info")
            
            print_section("Multi-Array Fusion")
            
            # Create fusion engine
            fusion = ShadowFusionEngine()
            
            # Simulate 3 arrays detecting same object
            array_positions = [
                np.array([0.0, 0.0]),
                np.array([1.0, 0.0]),
                np.array([0.5, 0.866])
            ]
            
            # Simulate detections (same object from different views)
            detections = []
            for i, pos in enumerate(array_positions):
                detection = {
                    'array_id': f'array_{i}',
                    'array_position': pos,
                    'contour': np.array([[0.05, 0.0], [0.0, 0.05], [-0.05, 0.0], [0.0, -0.05]]) + pos,
                    'confidence': 0.9 - i * 0.05,
                    'timestamp': time.time()
                }
                detections.append(detection)
            
            # Fuse detections
            start = time.perf_counter()
            fused = fusion.fuse_detections(detections)
            elapsed = (time.perf_counter() - start) * 1000
            
            print_result("Input arrays", str(len(detections)), "info")
            print_result("Fused objects", str(len(fused)), "info")
            print_result("Fusion time", f"{elapsed:.2f} ms", "pass" if elapsed < 5 else "warn")
            
            print_section("Global Shadow Map")
            
            # Create global map
            gmap = GlobalShadowMap()
            
            # Update with detections
            for detection in detections:
                gmap.update(detection)
            
            objects = gmap.get_all_objects()
            print_result("Tracked objects", str(len(objects)), "info")
            print_result("Global coverage", f"{gmap.get_coverage_fraction()*100:.1f}%", "info")
            
            ptp.stop()
            
            if self.run_benchmarks:
                print_section("Benchmarks")
                
                # Simulate 8 arrays
                times = []
                for _ in range(100):
                    test_detections = [
                        {'array_id': f'array_{i}', 'confidence': 0.9}
                        for i in range(8)
                    ]
                    start = time.perf_counter()
                    fusion.fuse_detections(test_detections)
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                
                mean_time = np.mean(times)
                print_result("8-array fusion", f"{mean_time:.2f} ms", "pass" if mean_time < 20 else "warn")
            
            self.results['distributed_network'] = {
                'status': 'PASS',
                'arrays': len(detections),
                'objects': len(objects),
                'fusion_ms': elapsed
            }
            
            print_success("Distributed Network demo complete")
            return self.results['distributed_network']
            
        except Exception as e:
            print_error(f"Distributed Network failed: {e}")
            self.results['distributed_network'] = {'status': 'FAIL', 'error': str(e)}
            return self.results['distributed_network']
    
    def demo_hal_sim2real(self) -> Dict:
        """
        Feature 4: HAL + Sim-to-Real Bridge
        
        Demonstrates hardware abstraction and mode switching.
        """
        print_header("FEATURE 4: HAL + SIM-TO-REAL BRIDGE")
        
        try:
            from hal.factory import create_microphone_array, create_glove
            from sim2real.bridge import SimToRealBridge, BridgeMode
            
            print_section("Simulation Mode")
            
            # Create simulated hardware
            sim_mics = create_microphone_array("sim")
            sim_glove = create_glove("sim")
            
            print_result("Microphone array", "Simulated", "info")
            print_result("Glove", "Simulated", "info")
            
            # Start streaming
            sim_mics.start_stream()
            sim_data = sim_mics.read(1024)
            sim_mics.stop_stream()
            
            print_result("Simulated samples", str(len(sim_data)), "info")
            print_result("Simulated shape", str(sim_data.shape), "info")
            
            print_section("Sim-to-Real Bridge")
            
            # Create bridge in sim mode
            bridge = SimToRealBridge(mode=BridgeMode.SIMULATION)
            
            # Process through bridge
            start = time.perf_counter()
            validated = bridge.process_microphone_data(sim_data)
            elapsed = (time.perf_counter() - start) * 1000
            
            print_result("Bridge mode", "SIMULATION", "info")
            print_result("Validation", "✓ Passed" if validated is not None else "✗ Failed", "pass" if validated is not None else "warn")
            print_result("Processing time", f"{elapsed:.2f} ms", "pass" if elapsed < 1 else "warn")
            
            print_section("Mode Switching")
            
            # Switch to real mode (will use mock hardware)
            bridge.set_mode(BridgeMode.REAL)
            print_result("Switched to", "REAL (mock)", "info")
            
            # Hardware info
            hw_info = bridge.get_hardware_info()
            print_result("Hardware type", hw_info.get('microphone_array', 'unknown'), "info")
            print_result("Calibration", "Valid" if hw_info.get('calibration_valid') else "Invalid", "pass" if hw_info.get('calibration_valid') else "warn")
            
            if self.run_benchmarks:
                print_section("Benchmarks")
                
                # Benchmark mode switching
                times = []
                for _ in range(100):
                    start = time.perf_counter()
                    bridge.set_mode(BridgeMode.SIMULATION)
                    bridge.set_mode(BridgeMode.REAL)
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                
                mean_time = np.mean(times)
                print_result("Mode switch", f"{mean_time:.3f} ms", "pass" if mean_time < 10 else "warn")
            
            self.results['hal_sim2real'] = {
                'status': 'PASS',
                'mode': 'SIMULATION',
                'validation': validated is not None,
                'switching_ms': mean_time if self.run_benchmarks else None
            }
            
            print_success("HAL + Sim-to-Real demo complete")
            return self.results['hal_sim2real']
            
        except Exception as e:
            print_error(f"HAL Sim-to-Real failed: {e}")
            self.results['hal_sim2real'] = {'status': 'FAIL', 'error': str(e)}
            return self.results['hal_sim2real']
    
    def demo_intelligence_layer(self) -> Dict:
        """
        Feature 5: Intelligence Layer
        
        Demonstrates edge AI intent classification.
        """
        print_header("FEATURE 5: INTELLIGENCE LAYER")
        
        try:
            from model import IntentClassifier, ModelConfig
            
            print_section("Model Architecture")
            
            # Create model
            config = ModelConfig()
            classifier = IntentClassifier(config)
            
            params = classifier.count_parameters()
            size_kb = classifier.get_model_size_kb()
            
            print_result("Parameters", f"{params:,}", "info")
            print_result("Model size", f"{size_kb:.2f} KB", "pass" if size_kb < 1024 else "warn")
            print_result("Input shape", "(64, 3)", "info")
            print_result("Output classes", "3 (hand, tool, other)", "info")
            
            print_section("Intent Classification")
            
            # Generate test contours for each class
            np.random.seed(42)
            
            # Hand-like contour
            t = np.linspace(0, 2*np.pi, 64, endpoint=False)
            x = 0.05 * np.cos(t) + 0.01 * np.sin(5*t)
            y = 0.06 * np.sin(t) + 0.005 * np.cos(7*t)
            confidence = 0.8 + 0.2 * np.random.random(64)
            hand_contour = np.column_stack([x, y, confidence])
            
            # Predict
            start = time.perf_counter()
            result = classifier.predict(hand_contour)
            elapsed = (time.perf_counter() - start) * 1000
            
            print_result("Predicted class", result['class'], "info")
            print_result("Confidence", f"{result['confidence']:.3f}", "pass" if result['confidence'] > 0.7 else "warn")
            print_result("Inference time", f"{elapsed:.2f} ms", "pass" if elapsed < 5 else "warn")
            
            print("  Class probabilities:")
            for name, prob in result['probabilities'].items():
                bar = '█' * int(prob * 20)
                print(f"    {name:10} {prob:.3f} {bar}")
            
            if self.run_benchmarks:
                print_section("Benchmarks")
                
                # Benchmark inference
                times = []
                for _ in range(100):
                    start = time.perf_counter()
                    classifier.predict(hand_contour)
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                
                mean_time = np.mean(times)
                p99_time = np.percentile(times, 99)
                
                print_result("Mean inference", f"{mean_time:.2f} ms", "pass" if mean_time < 5 else "warn")
                print_result("P99 inference", f"{p99_time:.2f} ms", "pass" if p99_time < 10 else "warn")
            
            self.results['intelligence_layer'] = {
                'status': 'PASS',
                'predicted_class': result['class'],
                'confidence': result['confidence'],
                'inference_ms': elapsed,
                'model_size_kb': size_kb
            }
            
            print_success("Intelligence Layer demo complete")
            return self.results['intelligence_layer']
            
        except Exception as e:
            print_error(f"Intelligence Layer failed: {e}")
            self.results['intelligence_layer'] = {'status': 'FAIL', 'error': str(e)}
            return self.results['intelligence_layer']
    
    def run_all(self):
        """Run all feature demonstrations."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔" + "═"*68 + "╗")
        print("║" + " SHADOW PRINCIPLE PLATFORM - FEATURE DEMONSTRATION ".center(68) + "║")
        print("║" + " v2.0 (Steroids Edition) ".center(68) + "║")
        print("╚" + "═"*68 + "╝")
        print(f"{Colors.END}\n")
        
        print(f"Configuration:")
        print(f"  Benchmarks: {'Enabled' if self.run_benchmarks else 'Disabled'}")
        print(f"  Visualization: {'Enabled' if self.visualize else 'Disabled'}")
        
        # Run all demos
        self.demo_universal_engine()
        self.demo_shadow_mesh_3d()
        self.demo_distributed_network()
        self.demo_hal_sim2real()
        self.demo_intelligence_layer()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print final summary."""
        print_header("DEMONSTRATION SUMMARY")
        
        print(f"\n{Colors.BOLD}Feature Results:{Colors.END}\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get('status') == 'PASS')
        
        for name, result in self.results.items():
            status = result.get('status', 'UNKNOWN')
            color = Colors.GREEN if status == 'PASS' else Colors.RED if status == 'FAIL' else Colors.YELLOW
            
            print(f"  {name.replace('_', ' ').title():<30} {color}{status}{Colors.END}")
            
            if status == 'PASS':
                # Print key metrics
                for key, value in result.items():
                    if key not in ['status', 'error'] and value is not None:
                        if isinstance(value, float):
                            print(f"    └─ {key}: {value:.3f}")
                        else:
                            print(f"    └─ {key}: {value}")
            elif status == 'FAIL':
                print(f"    └─ Error: {result.get('error', 'Unknown')}")
        
        print(f"\n{Colors.BOLD}Overall: {passed}/{total} features passed{Colors.END}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL FEATURES OPERATIONAL{Colors.END}")
        elif passed >= total // 2:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ PARTIAL SUCCESS - Review failures{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SIGNIFICANT ISSUES - Investigation required{Colors.END}")
        
        print(f"\n{Colors.CYAN}For more information, see individual README files:{Colors.END}")
        print("  - feature-universal-engine/README.md")
        print("  - feature-shadow-mesh-3d/README.md")
        print("  - feature-distributed-network/README.md")
        print("  - feature-hal-sim2real/README.md")
        print("  - feature-intelligence-layer/README.md")
        
        print(f"\n{Colors.HEADER}{'='*70}{Colors.END}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Shadow Principle Platform - Feature Demonstration'
    )
    parser.add_argument(
        '--no-benchmark', 
        action='store_true',
        help='Disable performance benchmarks'
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Enable visualizations (if available)'
    )
    
    args = parser.parse_args()
    
    demo = FeatureDemo(
        run_benchmarks=not args.no_benchmark,
        visualize=args.visualize
    )
    
    demo.run_all()


if __name__ == "__main__":
    main()
