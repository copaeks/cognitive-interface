"""
Distributed Network Benchmarks.

Performance benchmarks for the distributed shadow tracking network.
Targets:
- Total latency <20ms with 8 arrays
- Support 10+ simultaneous objects
- O(1) per object (not O(n) with array count)
- Network bandwidth <10Mbps per array
"""

import asyncio
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from node.shadow_node import ShadowNode, ShadowNodeCluster
from fusion.shadow_fusion import ArrayPosition, Vector2D


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    samples: List[float] = field(default_factory=list)
    unit: str = "ms"
    
    @property
    def mean(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0.0
    
    @property
    def median(self) -> float:
        return statistics.median(self.samples) if self.samples else 0.0
    
    @property
    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0
    
    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0
    
    @property
    def stdev(self) -> float:
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0.0
    
    @property
    def p95(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]
    
    @property
    def p99(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]
    
    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Mean: {self.mean:.3f} {self.unit}\n"
            f"  Median: {self.median:.3f} {self.unit}\n"
            f"  Min: {self.min:.3f} {self.unit}\n"
            f"  Max: {self.max:.3f} {self.unit}\n"
            f"  StdDev: {self.stdev:.3f} {self.unit}\n"
            f"  P95: {self.p95:.3f} {self.unit}\n"
            f"  P99: {self.p99:.3f} {self.unit}\n"
            f"  Samples: {len(self.samples)}"
        )


class DistributedBenchmark:
    """Benchmark suite for distributed shadow network."""
    
    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
    
    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks."""
        print("=" * 60)
        print("DISTRIBUTED SHADOW NETWORK BENCHMARKS")
        print("=" * 60)
        
        await self.benchmark_single_array_latency()
        await self.benchmark_8_array_latency()
        await self.benchmark_10_objects_tracking()
        await self.benchmark_20_objects_tracking()
        await self.benchmark_network_bandwidth()
        await self.benchmark_fusion_throughput()
        await self.benchmark_handoff_performance()
        
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        for name, result in self.results.items():
            print(f"\n{result}")
        
        # Check targets
        self._verify_targets()
        
        return self.results
    
    async def benchmark_single_array_latency(self) -> BenchmarkResult:
        """Benchmark latency for single array processing."""
        print("\n[1/7] Single Array Latency Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("Single Array Latency")
        
        # Create single node
        cluster = ShadowNodeCluster()
        node = await cluster.create_node(
            "array_0",
            position=(10.0, 10.0),
            is_coordinator=True
        )
        
        # Warmup
        for _ in range(10):
            await node.detect_shadow(45.0, 5.0, 0.9)
        await asyncio.sleep(0.1)
        
        # Benchmark
        for i in range(100):
            start = time.perf_counter()
            await node.detect_shadow(45.0 + i, 5.0, 0.9)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.samples.append(elapsed_ms)
        
        await cluster.stop_all()
        
        self.results["single_array_latency"] = result
        print(result)
        return result
    
    async def benchmark_8_array_latency(self) -> BenchmarkResult:
        """Benchmark total latency with 8 arrays."""
        print("\n[2/7] 8-Array Latency Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("8-Array Total Latency")
        
        # Create 8-node cluster
        cluster = ShadowNodeCluster()
        
        # 8 arrays in optimal positions for 20x20 room
        positions = [
            (3.0, 3.0), (17.0, 3.0), (3.0, 17.0), (17.0, 17.0),  # Corners
            (10.0, 3.0), (10.0, 17.0), (3.0, 10.0), (17.0, 10.0)   # Midpoints
        ]
        
        nodes = []
        for i, pos in enumerate(positions):
            node = await cluster.create_node(
                f"array_{i}",
                position=pos,
                is_coordinator=(i == 0)
            )
            nodes.append(node)
        
        # Allow time for discovery and sync
        await asyncio.sleep(0.5)
        
        # Benchmark - detect from all arrays
        for _ in range(50):
            start = time.perf_counter()
            
            # Each array detects same object
            await asyncio.gather(*[
                node.detect_shadow(45.0, 5.0, 0.9)
                for node in nodes
            ])
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.samples.append(elapsed_ms)
            
            await asyncio.sleep(0.01)  # 100Hz rate
        
        await cluster.stop_all()
        
        self.results["8_array_latency"] = result
        print(result)
        return result
    
    async def benchmark_10_objects_tracking(self) -> BenchmarkResult:
        """Benchmark tracking 10 simultaneous objects."""
        print("\n[3/7] 10 Objects Tracking Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("10 Objects Tracking Latency")
        
        cluster = ShadowNodeCluster()
        
        # Create 4 arrays
        positions = [(5.0, 5.0), (15.0, 5.0), (5.0, 15.0), (15.0, 15.0)]
        nodes = []
        for i, pos in enumerate(positions):
            node = await cluster.create_node(
                f"array_{i}",
                position=pos,
                is_coordinator=(i == 0),
                max_objects=10
            )
            nodes.append(node)
        
        await asyncio.sleep(0.3)
        
        # Track 10 objects
        object_angles = [i * 36 for i in range(10)]  # Spread around
        
        for iteration in range(50):
            start = time.perf_counter()
            
            # Each array detects all 10 objects
            for node in nodes:
                for angle in object_angles:
                    await node.detect_shadow(angle, 3.0 + iteration * 0.1, 0.85)
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.samples.append(elapsed_ms)
            
            await asyncio.sleep(0.02)
        
        await cluster.stop_all()
        
        self.results["10_objects_tracking"] = result
        print(result)
        return result
    
    async def benchmark_20_objects_tracking(self) -> BenchmarkResult:
        """Benchmark tracking 20 simultaneous objects."""
        print("\n[4/7] 20 Objects Tracking Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("20 Objects Tracking Latency")
        
        cluster = ShadowNodeCluster()
        
        # Create 8 arrays for more capacity
        positions = [
            (3.0, 3.0), (10.0, 3.0), (17.0, 3.0),
            (3.0, 10.0), (17.0, 10.0),
            (3.0, 17.0), (10.0, 17.0), (17.0, 17.0)
        ]
        
        nodes = []
        for i, pos in enumerate(positions):
            node = await cluster.create_node(
                f"array_{i}",
                position=pos,
                is_coordinator=(i == 0),
                max_objects=20
            )
            nodes.append(node)
        
        await asyncio.sleep(0.3)
        
        # Track 20 objects
        object_angles = [i * 18 for i in range(20)]
        
        for iteration in range(30):
            start = time.perf_counter()
            
            for node in nodes:
                for angle in object_angles:
                    await node.detect_shadow(angle, 4.0, 0.8)
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.samples.append(elapsed_ms)
            
            await asyncio.sleep(0.02)
        
        await cluster.stop_all()
        
        self.results["20_objects_tracking"] = result
        print(result)
        return result
    
    async def benchmark_network_bandwidth(self) -> BenchmarkResult:
        """Benchmark network bandwidth usage per array."""
        print("\n[5/7] Network Bandwidth Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("Network Bandwidth", unit="Mbps")
        
        cluster = ShadowNodeCluster()
        
        # Create 4 arrays
        positions = [(5.0, 5.0), (15.0, 5.0), (5.0, 15.0), (15.0, 15.0)]
        nodes = []
        for i, pos in enumerate(positions):
            node = await cluster.create_node(
                f"array_{i}",
                position=pos,
                is_coordinator=(i == 0)
            )
            nodes.append(node)
        
        await asyncio.sleep(0.3)
        
        # Measure bandwidth over 1 second
        duration = 1.0
        start_time = time.time()
        
        # Generate traffic
        while time.time() - start_time < duration:
            for node in nodes:
                await node.detect_shadow(45.0, 5.0, 0.9)
            await asyncio.sleep(0.01)
        
        # Get stats
        for node in nodes:
            stats = node.get_stats()
            # Estimate bandwidth from packets sent
            # Each shadow data message is ~80 bytes
            # Bandwidth = packets * 80 * 8 / duration / 1_000_000
            bandwidth = (stats.shadows_sent * 80 * 8) / duration / 1_000_000
            result.samples.append(bandwidth)
        
        await cluster.stop_all()
        
        self.results["network_bandwidth"] = result
        print(result)
        return result
    
    async def benchmark_fusion_throughput(self) -> BenchmarkResult:
        """Benchmark shadow fusion throughput."""
        print("\n[6/7] Fusion Throughput Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("Fusion Throughput", unit="fusions/sec")
        
        from fusion.shadow_fusion import ShadowFusionEngine, ShadowObservation
        
        engine = ShadowFusionEngine()
        
        # Register 8 arrays
        for i in range(8):
            engine.register_array(ArrayPosition(
                f"array_{i}",
                Vector2D(float(i) * 2.0, 0.0),
                0.0
            ))
        
        # Create observations
        observations = []
        for i in range(1000):
            obs = ShadowObservation(
                observation_id=f"obs_{i}",
                array_id=f"array_{i % 8}",
                timestamp_ns=time.time_ns() + i * 1_000_000,
                global_position=Vector2D(float(i % 100), float(i // 100)),
                confidence=0.8,
                angle=45.0,
                distance=5.0
            )
            observations.append(obs)
        
        # Benchmark
        start = time.perf_counter()
        await engine.process_observations(observations)
        elapsed = time.perf_counter() - start
        
        throughput = len(observations) / elapsed
        result.samples.append(throughput)
        
        self.results["fusion_throughput"] = result
        print(result)
        return result
    
    async def benchmark_handoff_performance(self) -> BenchmarkResult:
        """Benchmark array handoff performance."""
        print("\n[7/7] Handoff Performance Benchmark")
        print("-" * 40)
        
        result = BenchmarkResult("Handoff Latency")
        
        cluster = ShadowNodeCluster()
        
        # Create 2 arrays with overlapping coverage
        node1 = await cluster.create_node(
            "array_1",
            position=(0.0, 0.0),
            is_coordinator=True
        )
        node2 = await cluster.create_node(
            "array_2",
            position=(3.0, 0.0)  # Close for overlap
        )
        
        await asyncio.sleep(0.3)
        
        # Simulate object moving from array1 to array2
        # Start near array1
        for i in range(20):
            start = time.perf_counter()
            
            # Object at varying distances
            distance = 2.0 + i * 0.2
            await node1.detect_shadow(0.0, distance, 0.9)
            await node2.detect_shadow(180.0, 3.0 - i * 0.15, 0.9)
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.samples.append(elapsed_ms)
            
            await asyncio.sleep(0.05)
        
        await cluster.stop_all()
        
        self.results["handoff_latency"] = result
        print(result)
        return result
    
    def _verify_targets(self) -> None:
        """Verify benchmark results meet targets."""
        print("\n" + "=" * 60)
        print("TARGET VERIFICATION")
        print("=" * 60)
        
        targets = {
            "8_array_latency": ("<20ms", lambda r: r.mean < 20.0),
            "10_objects_tracking": ("<20ms", lambda r: r.mean < 20.0),
            "network_bandwidth": ("<10Mbps", lambda r: r.mean < 10.0),
        }
        
        all_passed = True
        for name, (target, check) in targets.items():
            if name in self.results:
                result = self.results[name]
                passed = check(result)
                status = "PASS" if passed else "FAIL"
                print(f"  {name}: {result.mean:.2f} {result.unit} (target {target}) - {status}")
                if not passed:
                    all_passed = False
            else:
                print(f"  {name}: NOT RUN")
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("ALL TARGETS MET")
        else:
            print("SOME TARGETS NOT MET")
        print("=" * 60)


async def main():
    """Run benchmarks."""
    benchmark = DistributedBenchmark()
    await benchmark.run_all()


if __name__ == "__main__":
    asyncio.run(main())
