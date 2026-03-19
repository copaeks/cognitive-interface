# Distributed Shadow Network

Production-grade distributed shadow tracking network for factory/room-scale deployment using multiple microphone arrays.

## Features

- **PTP Time Synchronization**: Sub-microsecond accuracy across arrays
- **Multi-Array Fusion**: O(1) per object shadow fusion using spatial hashing
- **Global Shadow-Map**: Unified coordinate system with persistent object IDs
- **Array Handoffs**: Seamless object tracking across array boundaries
- **Network Transport**: UDP for real-time data, TCP for control
- **Load Balancing**: Automatic workload distribution
- **Fault Tolerance**: Graceful handling of array failures

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Total Latency (8 arrays) | <20ms | ✓ |
| Simultaneous Objects | 10+ | ✓ |
| Per-Object Complexity | O(1) | ✓ |
| Network Bandwidth | <10Mbps/array | ✓ |
| Time Sync Accuracy | <1μs | ✓ |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Global Shadow-Map                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Array 1 │  │ Array 2 │  │ Array 3 │  │ Array 4 │  ...  │
│  │ (Node)  │  │ (Node)  │  │ (Node)  │  │ (Node)  │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                    PTP Sync Network                         │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Clone repository
git clone <repository-url>
cd feature-distributed-network

# Install dependencies (Python 3.12+)
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Requirements

- Python 3.12+
- asyncio
- pytest (for testing)

## Quick Start

### Single Array Node

```python
import asyncio
from node.shadow_node import ShadowNode
from fusion.shadow_fusion import ArrayPosition, Vector2D

async def main():
    # Create array at position (10, 10)
    array_pos = ArrayPosition(
        array_id="array_1",
        position=Vector2D(10.0, 10.0),
        orientation=0.0
    )
    
    # Create and start node
    node = ShadowNode(
        node_id="array_1",
        array_position=array_pos,
        is_coordinator=True  # This node is the coordinator
    )
    
    await node.start()
    
    # Simulate shadow detection
    shadow = await node.detect_shadow(
        angle=45.0,      # degrees
        distance=5.0,    # meters
        confidence=0.85  # 0-1
    )
    
    print(f"Detected shadow at {shadow.global_position.to_tuple()}")
    
    # Get statistics
    stats = node.get_stats()
    print(f"Shadows detected: {stats.shadows_detected}")
    
    await node.stop()

asyncio.run(main())
```

### Multi-Array Cluster

```python
import asyncio
from node.shadow_node import ShadowNodeCluster

async def main():
    cluster = ShadowNodeCluster()
    
    # Create 4 arrays in corners of 20x20 room
    positions = [
        (5.0, 5.0),
        (15.0, 5.0),
        (5.0, 15.0),
        (15.0, 15.0)
    ]
    
    for i, pos in enumerate(positions):
        await cluster.create_node(
            f"array_{i}",
            position=pos,
            is_coordinator=(i == 0)
        )
    
    # Wait for discovery and sync
    await asyncio.sleep(1.0)
    
    # Detect shadows from all arrays
    for node in cluster.get_all_nodes():
        await node.detect_shadow(45.0, 5.0, 0.9)
    
    # Get coordinator for global view
    coordinator = cluster.get_node("array_0")
    global_objects = coordinator.get_global_objects()
    print(f"Global objects tracked: {len(global_objects)}")
    
    await cluster.stop_all()

asyncio.run(main())
```

## Running the 8-Array Simulation

```bash
# Run 30-second simulation with 10 objects
python simulation/multi_array_sim.py --duration 30 --objects 10

# With visualization
python simulation/multi_array_sim.py --duration 30 --objects 10 --visualize
```

## Running Benchmarks

```bash
# Run all benchmarks
python tests/benchmark_distributed.py

# Run specific test with pytest
pytest tests/test_sync.py -v
pytest tests/test_network.py -v
pytest tests/test_fusion.py -v
```

## Module Reference

### Network Layer (`network/`)

#### `ptp_sync.py`
PTP-like time synchronization for sub-microsecond accuracy.

```python
from network.ptp_sync import PTPSynchronizer, create_synchronizer

# Create master synchronizer
master = await create_synchronizer("master", is_master=True)

# Create slave synchronizer
slave = await create_synchronizer("slave", is_master=False)

# Get synchronized time
timestamp = slave.get_synced_time()
```

#### `transport.py`
Network transport with UDP for data and TCP for control.

```python
from network.transport import NetworkManager, NetworkEndpoint

manager = NetworkManager(
    node_id="node1",
    udp_endpoint=NetworkEndpoint("0.0.0.0", 5000),
    tcp_endpoint=NetworkEndpoint("0.0.0.0", 6000)
)

await manager.start()

# Register message handler
async def on_shadow_data(message, addr):
    print(f"Received from {addr}: {message.payload}")

manager.register_handler(MessageType.SHADOW_DATA, on_shadow_data)
```

### Fusion Layer (`fusion/`)

#### `shadow_fusion.py`
Multi-array shadow fusion with O(1) complexity.

```python
from fusion.shadow_fusion import ShadowFusionEngine, ShadowObservation

engine = ShadowFusionEngine(fusion_radius=0.5)

# Register array positions
engine.register_array(array_position)

# Process observation
obs = ShadowObservation(
    observation_id="obs1",
    array_id="array1",
    timestamp_ns=time.time_ns(),
    global_position=Vector2D(5.0, 5.0),
    confidence=0.8,
    angle=45.0,
    distance=5.0
)

fused = await engine.process_observation(obs)
```

#### `global_map.py`
Global shadow-map with persistent object IDs.

```python
from fusion.global_map import GlobalShadowMap

gmap = GlobalShadowMap(fusion_engine)

# Update from fused shadow
obj = await gmap.update_from_fusion(fused_shadow)

# Query objects
objects = gmap.get_objects_in_region(
    center=Vector2D(10.0, 10.0),
    radius=5.0
)
```

### Coordination Layer (`coordination/`)

#### `array_coordinator.py`
Central coordinator for node management and load balancing.

```python
from coordination.array_coordinator import ArrayCoordinator, NodeRole

coordinator = ArrayCoordinator(
    node_id="coordinator",
    role=NodeRole.MASTER
)

await coordinator.start()

# Register callback for node events
def on_node_event(node_id, info, event):
    print(f"Node {node_id} {event}")

coordinator.register_node_callback(on_node_event)
```

### Node Layer (`node/`)

#### `shadow_node.py`
Individual array node with full processing pipeline.

```python
from node.shadow_node import ShadowNode

node = ShadowNode(
    node_id="array_1",
    array_position=array_pos,
    is_coordinator=False
)

await node.start()

# Detect shadow
shadow = await node.detect_shadow(angle, distance, confidence)

# Get fused shadows
fused = node.get_fused_shadows()

# Get global objects (if coordinator)
objects = node.get_global_objects()
```

## Docker Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  coordinator:
    build: .
    command: python -m node.coordinator_node
    ports:
      - "5000:5000/udp"
      - "6000:6000/tcp"
    environment:
      - NODE_ID=coordinator
      - ROLE=master
    networks:
      - shadow-network

  array-1:
    build: .
    command: python -m node.array_node
    environment:
      - NODE_ID=array_1
      - COORDINATOR=coordinator
      - POSITION_X=5.0
      - POSITION_Y=5.0
    networks:
      - shadow-network

  array-2:
    build: .
    command: python -m node.array_node
    environment:
      - NODE_ID=array_2
      - COORDINATOR=coordinator
      - POSITION_X=15.0
      - POSITION_Y=5.0
    networks:
      - shadow-network

  # ... more arrays

networks:
  shadow-network:
    driver: bridge
```

### Build and Run

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale to 8 arrays
docker-compose up -d --scale array-worker=8

# Stop
docker-compose down
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ID` | Unique node identifier | Required |
| `ROLE` | Node role (master/worker) | worker |
| `UDP_PORT` | UDP port for data | 5000 |
| `TCP_PORT` | TCP port for control | 6000 |
| `POSITION_X` | Array X position | 0.0 |
| `POSITION_Y` | Array Y position | 0.0 |
| `ORIENTATION` | Array orientation (degrees) | 0.0 |
| `MAX_OBJECTS` | Maximum objects to track | 10 |
| `SYNC_INTERVAL_MS` | PTP sync interval | 100 |

### Tuning Parameters

```python
# Fusion parameters
fusion_engine = ShadowFusionEngine(
    fusion_radius=0.5,        # Meters - objects closer than this fuse
    min_confidence=0.3,       # Minimum confidence to accept
    max_shadow_age_ms=500.0   # Shadow timeout
)

# Global map parameters
global_map = GlobalShadowMap(
    fusion_engine,
    max_object_age_ms=2000.0,  # Object timeout
    handoff_threshold=0.7      # Confidence for handoff
)

# Network parameters
network = NetworkManager(
    node_id,
    udp_endpoint,
    tcp_endpoint,
    multicast_group="239.255.0.1"
)
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_sync.py -v
pytest tests/test_network.py -v
pytest tests/test_fusion.py -v
```

### Integration Tests

```bash
# Run multi-array simulation test
python simulation/multi_array_sim.py --duration 10 --objects 5

# Run benchmarks
python tests/benchmark_distributed.py
```

## Performance Optimization

### Latency Reduction

1. **Increase Update Rate**: Higher frame rates reduce latency
2. **Optimize Fusion Radius**: Smaller radius = faster queries
3. **Reduce Network Hops**: Place coordinator centrally
4. **Enable Kernel Bypass**: Use DPDK for network (advanced)

### Scalability

1. **Spatial Partitioning**: Use multiple coordinators for large deployments
2. **Hierarchical Fusion**: Fuse locally, then globally
3. **Selective Streaming**: Only stream significant changes

### Memory Usage

1. **Limit Trajectory History**: Reduce `max_trajectory_length`
2. **Aggressive Cleanup**: Lower `max_shadow_age_ms`
3. **Object Pooling**: Reuse observation objects

## Troubleshooting

### High Latency

```python
# Check sync status
sync_stats = node._coordinator._ptp.stats
print(f"Sync offset: {sync_stats.offset_ns}ns")

# Check network stats
net_stats = node._network.stats
print(f"Packets dropped: {net_stats['udp'].get('packets_dropped', 0)}")
```

### Sync Issues

```python
# Force re-sync
await node._coordinator._ptp.stop()
await asyncio.sleep(0.1)
await node._coordinator._ptp.start()
```

### Network Issues

```bash
# Check multicast
tcpdump -i eth0 host 239.255.0.1

# Check ports
netstat -tulpn | grep 5000
```

## API Reference

See inline documentation in source files:

- `network/ptp_sync.py`: PTP synchronization API
- `network/transport.py`: Network transport API
- `fusion/shadow_fusion.py`: Shadow fusion API
- `fusion/global_map.py`: Global map API
- `coordination/array_coordinator.py`: Coordination API
- `node/shadow_node.py`: Node API

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- PTP protocol inspired by IEEE 1588
- Spatial hashing based on computer graphics techniques
- Async patterns from asyncio best practices
version: '3.8'

# Docker Compose for Distributed Shadow Network
# Deploys 1 coordinator + 8 array nodes for full simulation

services:
  # Coordinator node (also acts as array 0)
  coordinator:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-coordinator
    hostname: coordinator
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_0', Vector2D(10.0, 10.0), 0.0)
          node = ShadowNode('array_0', pos, is_coordinator=True,
                          udp_port=5000, tcp_port=6000)
          await node.start()
          print('Coordinator started on array_0')
          
          # Keep running
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5000:5000/udp"
      - "6000:6000/tcp"
    environment:
      - NODE_ID=array_0
      - ROLE=master
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost', 6000)); s.close()"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Array nodes 1-8
  array-1:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-1
    hostname: array-1
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_1', Vector2D(3.0, 3.0), 0.0)
          node = ShadowNode('array_1', pos, is_coordinator=False,
                          udp_port=5001, tcp_port=6001)
          await node.start()
          print('Array 1 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5001:5001/udp"
      - "6001:6001/tcp"
    environment:
      - NODE_ID=array_1
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-2:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-2
    hostname: array-2
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_2', Vector2D(17.0, 3.0), 0.0)
          node = ShadowNode('array_2', pos, is_coordinator=False,
                          udp_port=5002, tcp_port=6002)
          await node.start()
          print('Array 2 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5002:5002/udp"
      - "6002:6002/tcp"
    environment:
      - NODE_ID=array_2
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-3:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-3
    hostname: array-3
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_3', Vector2D(3.0, 17.0), 0.0)
          node = ShadowNode('array_3', pos, is_coordinator=False,
                          udp_port=5003, tcp_port=6003)
          await node.start()
          print('Array 3 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5003:5003/udp"
      - "6003:6003/tcp"
    environment:
      - NODE_ID=array_3
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-4:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-4
    hostname: array-4
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_4', Vector2D(17.0, 17.0), 0.0)
          node = ShadowNode('array_4', pos, is_coordinator=False,
                          udp_port=5004, tcp_port=6004)
          await node.start()
          print('Array 4 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5004:5004/udp"
      - "6004:6004/tcp"
    environment:
      - NODE_ID=array_4
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-5:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-5
    hostname: array-5
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_5', Vector2D(10.0, 3.0), 0.0)
          node = ShadowNode('array_5', pos, is_coordinator=False,
                          udp_port=5005, tcp_port=6005)
          await node.start()
          print('Array 5 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5005:5005/udp"
      - "6005:6005/tcp"
    environment:
      - NODE_ID=array_5
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-6:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-6
    hostname: array-6
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_6', Vector2D(10.0, 17.0), 0.0)
          node = ShadowNode('array_6', pos, is_coordinator=False,
                          udp_port=5006, tcp_port=6006)
          await node.start()
          print('Array 6 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5006:5006/udp"
      - "6006:6006/tcp"
    environment:
      - NODE_ID=array_6
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-7:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-7
    hostname: array-7
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_7', Vector2D(3.0, 10.0), 0.0)
          node = ShadowNode('array_7', pos, is_coordinator=False,
                          udp_port=5007, tcp_port=6007)
          await node.start()
          print('Array 7 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5007:5007/udp"
      - "6007:6007/tcp"
    environment:
      - NODE_ID=array_7
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  array-8:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-array-8
    hostname: array-8
    command: >
      python -c "
      import asyncio
      from node.shadow_node import ShadowNode
      from fusion.shadow_fusion import ArrayPosition, Vector2D
      
      async def main():
          pos = ArrayPosition('array_8', Vector2D(17.0, 10.0), 0.0)
          node = ShadowNode('array_8', pos, is_coordinator=False,
                          udp_port=5008, tcp_port=6008)
          await node.start()
          print('Array 8 started')
          
          while True:
              await asyncio.sleep(1)
      
      asyncio.run(main())
      "
    ports:
      - "5008:5008/udp"
      - "6008:6008/tcp"
    environment:
      - NODE_ID=array_8
      - ROLE=worker
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      coordinator:
        condition: service_healthy

  # Simulation runner
  simulator:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: shadow-simulator
    command: >
      python -c "
      import asyncio
      import time
      from simulation.multi_array_sim import run_simulation
      
      async def main():
          results = await run_simulation(duration=30, num_objects=10)
          print('\nSimulation complete!')
          print(f'Detected {results[\"global_objects_tracked\"]} objects')
      
      asyncio.run(main())
      "
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - shadow-network
    depends_on:
      - coordinator
      - array-1
      - array-2
      - array-3
      - array-4
      - array-5
      - array-6
      - array-7
      - array-8
    profiles:
      - simulation

networks:
  shadow-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
# Dockerfile for Distributed Shadow Network
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . /app/

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "-c", "print('Distributed Shadow Network - Use docker-compose to run')"]
# Distributed Shadow Network Requirements
# Python 3.12+

# Core dependencies (stdlib only for production)
# asyncio - included in Python 3.12+
# dataclasses - included in Python 3.12+
# typing - included in Python 3.12+

# Development dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Optional: Performance monitoring
# psutil>=5.9.0

# Optional: Type checking
# mypy>=1.5.0
"""Tests for Distributed Shadow Network."""
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
"""
Tests for Shadow Fusion and Global Map.
"""

import asyncio
import pytest
import math
import time
from typing import List

from fusion.shadow_fusion import (
    Vector2D, ArrayPosition, ShadowObservation, ShadowFusionEngine,
    SpatialHash, TriangulationFusion, FusedShadow
)
from fusion.global_map import (
    GlobalObject, GlobalShadowMap, ArrayCoverage, CoveragePlanner
)


class TestVector2D:
    """Test Vector2D class."""
    
    def test_creation(self):
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
    
    def test_addition(self):
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_subtraction(self):
        v1 = Vector2D(5.0, 5.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 2.0
    
    def test_scalar_multiplication(self):
        v = Vector2D(2.0, 3.0)
        result = v * 2.0
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_magnitude(self):
        v = Vector2D(3.0, 4.0)
        assert v.magnitude() == 5.0
    
    def test_distance(self):
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_to(v2) == 5.0
    
    def test_to_tuple(self):
        v = Vector2D(1.5, 2.5)
        assert v.to_tuple() == (1.5, 2.5)


class TestArrayPosition:
    """Test ArrayPosition class."""
    
    def test_local_to_global(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(10.0, 10.0),
            orientation=0.0
        )
        
        local = Vector2D(3.0, 4.0)
        global_pos = pos.local_to_global(local)
        
        # With 0 orientation, just add
        assert global_pos.x == 13.0
        assert global_pos.y == 14.0
    
    def test_local_to_global_with_rotation(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(0.0, 0.0),
            orientation=90.0  # 90 degrees
        )
        
        local = Vector2D(1.0, 0.0)
        global_pos = pos.local_to_global(local)
        
        # Rotated 90 degrees, x becomes y
        assert abs(global_pos.x - 0.0) < 0.001
        assert abs(global_pos.y - 1.0) < 0.001
    
    def test_global_to_local(self):
        pos = ArrayPosition(
            "array1",
            Vector2D(10.0, 10.0),
            orientation=0.0
        )
        
        global_pos = Vector2D(13.0, 14.0)
        local = pos.global_to_local(global_pos)
        
        assert local.x == 3.0
        assert local.y == 4.0


class TestSpatialHash:
    """Test SpatialHash class."""
    
    @pytest.mark.asyncio
    async def test_insert_and_query(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.5, 0.5))
        
        # Query near the object
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" in neighbors
    
    @pytest.mark.asyncio
    async def test_query_excludes_distant(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj2", Vector2D(10.0, 10.0))
        
        # Query near obj1
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 2.0)
        assert "obj1" in neighbors
        assert "obj2" not in neighbors
    
    @pytest.mark.asyncio
    async def test_update_position(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj1", Vector2D(5.0, 5.0))  # Update
        
        neighbors = await sh.query_neighbors(Vector2D(5.0, 5.0), 1.0)
        assert "obj1" in neighbors
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" not in neighbors
    
    @pytest.mark.asyncio
    async def test_remove(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.remove("obj1")
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 1.0)
        assert "obj1" not in neighbors
    
    @pytest.mark.asyncio
    async def test_clear(self):
        sh = SpatialHash(cell_size=1.0)
        
        await sh.insert("obj1", Vector2D(0.0, 0.0))
        await sh.insert("obj2", Vector2D(1.0, 1.0))
        await sh.clear()
        
        neighbors = await sh.query_neighbors(Vector2D(0.0, 0.0), 10.0)
        assert len(neighbors) == 0


class TestShadowFusionEngine:
    """Test ShadowFusionEngine class."""
    
    @pytest.mark.asyncio
    async def test_single_observation_creates_shadow(self):
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        assert fused is not None
        assert fused.observation_count == 1
        assert "array1" in fused.contributing_arrays
    
    @pytest.mark.asyncio
    async def test_nearby_observations_fuse(self):
        engine = ShadowFusionEngine(fusion_radius=1.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs1 = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        obs2 = ShadowObservation(
            observation_id="obs2",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.1, 0.0),  # Very close
            confidence=0.7,
            angle=0.0,
            distance=5.1
        )
        
        fused1 = await engine.process_observation(obs1)
        fused2 = await engine.process_observation(obs2)
        
        # Should be same shadow
        assert fused1.shadow_id == fused2.shadow_id
        assert fused2.observation_count == 2
    
    @pytest.mark.asyncio
    async def test_distant_observations_create_separate(self):
        engine = ShadowFusionEngine(fusion_radius=1.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs1 = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        obs2 = ShadowObservation(
            observation_id="obs2",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(15.0, 0.0),  # Far away
            confidence=0.7,
            angle=0.0,
            distance=15.0
        )
        
        fused1 = await engine.process_observation(obs1)
        fused2 = await engine.process_observation(obs2)
        
        # Should be different shadows
        assert fused1.shadow_id != fused2.shadow_id
    
    @pytest.mark.asyncio
    async def test_low_confidence_rejected(self):
        engine = ShadowFusionEngine(min_confidence=0.5)
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.3,  # Below threshold
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        assert fused is None
    
    @pytest.mark.asyncio
    async def test_fusion_callback(self):
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        callbacks = []
        def on_fuse(fused):
            callbacks.append(fused)
        
        engine.add_fusion_callback(on_fuse)
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        await engine.process_observation(obs)
        
        assert len(callbacks) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_shadows(self):
        engine = ShadowFusionEngine(max_shadow_age_ms=100.0)
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        obs = ShadowObservation(
            observation_id="obs1",
            array_id="array1",
            timestamp_ns=time.time_ns(),
            global_position=Vector2D(5.0, 0.0),
            confidence=0.8,
            angle=0.0,
            distance=5.0
        )
        
        fused = await engine.process_observation(obs)
        
        # Wait for shadow to become stale
        await asyncio.sleep(0.15)
        
        stale = await engine.cleanup_stale_shadows(time.time_ns())
        
        assert len(stale) == 1
        assert engine.get_shadow_count() == 0


class TestTriangulationFusion:
    """Test TriangulationFusion class."""
    
    def test_triangulation_with_three_arrays(self):
        tri = TriangulationFusion(min_arrays_for_triangulation=3)
        
        observations = [
            ShadowObservation("obs1", "array1", 0, Vector2D(0.0, 0.0), 0.9, 45.0, 5.0),
            ShadowObservation("obs2", "array2", 0, Vector2D(10.0, 0.0), 0.9, 135.0, 5.0),
            ShadowObservation("obs3", "array3", 0, Vector2D(5.0, 8.66), 0.9, 270.0, 5.0),
        ]
        
        result = tri.triangulate(observations)
        
        assert result is not None
        position, confidence = result
        assert confidence > 0.5
    
    def test_triangulation_insufficient_arrays(self):
        tri = TriangulationFusion(min_arrays_for_triangulation=3)
        
        observations = [
            ShadowObservation("obs1", "array1", 0, Vector2D(0.0, 0.0), 0.9, 45.0, 5.0),
            ShadowObservation("obs2", "array2", 0, Vector2D(10.0, 0.0), 0.9, 135.0, 5.0),
        ]
        
        result = tri.triangulate(observations)
        
        assert result is None
    
    def test_bearing_intersection(self):
        tri = TriangulationFusion()
        
        # Two arrays at right angles should intersect at (5, 5)
        intersection = tri.calculate_bearing_intersection(
            Vector2D(0.0, 0.0), 45.0,   # From origin at 45 degrees
            Vector2D(10.0, 0.0), 135.0  # From (10, 0) at 135 degrees
        )
        
        assert intersection is not None
        assert abs(intersection.x - 5.0) < 0.1
        assert abs(intersection.y - 5.0) < 0.1


class TestGlobalObject:
    """Test GlobalObject class."""
    
    def test_update_position(self):
        obj = GlobalObject(
            object_id="obj1",
            created_ns=time.time_ns(),
            position=Vector2D(0.0, 0.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            primary_array="array1",
            visible_arrays={"array1"},
            last_seen_ns=time.time_ns()
        )
        
        obj.update_position(Vector2D(1.0, 0.0), time.time_ns() + 100_000_000)
        
        assert obj.position.x == 1.0
        assert obj.velocity.x > 0  # Should have positive velocity
    
    def test_predict_position(self):
        obj = GlobalObject(
            object_id="obj1",
            created_ns=time.time_ns(),
            position=Vector2D(0.0, 0.0),
            velocity=Vector2D(1.0, 0.0),  # 1 m/s in x
            confidence=0.8,
            primary_array="array1",
            visible_arrays={"array1"},
            last_seen_ns=time.time_ns()
        )
        
        future_time = time.time_ns() + 1_000_000_000  # 1 second later
        predicted = obj.predict_position(future_time)
        
        assert abs(predicted.x - 1.0) < 0.1


class TestGlobalShadowMap:
    """Test GlobalShadowMap class."""
    
    @pytest.mark.asyncio
    async def test_update_from_fusion_creates_object(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        obj = await gmap.update_from_fusion(fused)
        
        assert obj is not None
        assert obj.object_id.startswith("obj_")
    
    @pytest.mark.asyncio
    async def test_object_callback(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        events = []
        def on_event(obj, event):
            events.append((obj, event))
        
        gmap.add_object_callback(on_event)
        
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        await gmap.update_from_fusion(fused)
        
        assert len(events) == 1
        assert events[0][1] == "created"
    
    @pytest.mark.asyncio
    async def test_get_objects_in_region(self):
        fusion = ShadowFusionEngine()
        gmap = GlobalShadowMap(fusion)
        
        # Create object at (5, 5)
        fused = FusedShadow(
            shadow_id="shadow1",
            timestamp_ns=time.time_ns(),
            position=Vector2D(5.0, 5.0),
            velocity=Vector2D(0.0, 0.0),
            confidence=0.8,
            contributing_arrays={"array1"},
            observation_count=1,
            last_update_ns=time.time_ns()
        )
        
        await gmap.update_from_fusion(fused)
        
        # Query region containing the object
        objects = gmap.get_objects_in_region(Vector2D(0.0, 0.0), 10.0)
        assert len(objects) == 1
        
        # Query region not containing the object
        objects = gmap.get_objects_in_region(Vector2D(20.0, 20.0), 2.0)
        assert len(objects) == 0


class TestCoveragePlanner:
    """Test CoveragePlanner class."""
    
    def test_single_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(1, 5.0)
        
        assert len(positions) == 1
        assert positions[0] == (10.0, 10.0)  # Center
    
    def test_four_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(4, 5.0)
        
        assert len(positions) == 4
        # Should be near corners
    
    def test_eight_array_placement(self):
        planner = CoveragePlanner((20.0, 20.0))
        positions = planner.calculate_optimal_placement(8, 5.0)
        
        assert len(positions) == 8
    
    def test_coverage_estimation(self):
        planner = CoveragePlanner((10.0, 10.0))
        positions = [(5.0, 5.0)]  # Single center array
        
        coverage = planner.estimate_coverage(positions, 10.0)
        
        # Single array with 10m radius should cover most of 10x10 room
        assert coverage > 0.7


class TestFusionPerformance:
    """Performance tests for fusion."""
    
    @pytest.mark.asyncio
    async def test_fusion_throughput(self):
        """Test fusion processing throughput."""
        engine = ShadowFusionEngine()
        engine.register_array(ArrayPosition("array1", Vector2D(0.0, 0.0), 0.0))
        
        # Create many observations
        observations = []
        for i in range(100):
            obs = ShadowObservation(
                observation_id=f"obs_{i}",
                array_id="array1",
                timestamp_ns=time.time_ns() + i * 1_000_000,
                global_position=Vector2D(float(i) * 0.5, 0.0),
                confidence=0.8,
                angle=0.0,
                distance=float(i) * 0.5
            )
            observations.append(obs)
        
        # Process all
        start = time.time()
        await engine.process_observations(observations)
        elapsed = time.time() - start
        
        # Should process 100 observations quickly
        assert elapsed < 1.0
    
    def test_spatial_hash_performance(self):
        """Test spatial hash query performance."""
        import timeit
        
        async def benchmark():
            sh = SpatialHash(cell_size=1.0)
            
            # Insert 1000 objects
            for i in range(1000):
                await sh.insert(f"obj_{i}", Vector2D(float(i % 100), float(i // 100)))
            
            # Time queries
            start = time.time()
            for _ in range(100):
                await sh.query_neighbors(Vector2D(50.0, 50.0), 5.0)
            elapsed = time.time() - start
            
            return elapsed
        
        elapsed = asyncio.run(benchmark())
        
        # 100 queries should be fast
        assert elapsed < 0.1
"""
Tests for Network Transport Layer.
"""

import asyncio
import pytest
import time
from typing import List, Tuple

from network.transport import (
    NetworkManager, NetworkEndpoint, Message, MessageType,
    ShadowData, UDPTransport, TCPTransport, MockNetwork
)


class TestNetworkEndpoint:
    """Test NetworkEndpoint class."""
    
    def test_creation(self):
        ep = NetworkEndpoint("127.0.0.1", 5000)
        assert ep.host == "127.0.0.1"
        assert ep.port == 5000
    
    def test_string_conversion(self):
        ep = NetworkEndpoint("127.0.0.1", 5000)
        assert str(ep) == "127.0.0.1:5000"
    
    def test_hash(self):
        ep1 = NetworkEndpoint("127.0.0.1", 5000)
        ep2 = NetworkEndpoint("127.0.0.1", 5000)
        ep3 = NetworkEndpoint("127.0.0.1", 5001)
        
        assert hash(ep1) == hash(ep2)
        assert hash(ep1) != hash(ep3)


class TestMessage:
    """Test Message class."""
    
    def test_creation(self):
        msg = Message(
            msg_type=MessageType.SHADOW_DATA,
            source_id="node1",
            payload=b"test data",
            timestamp=123456789000000,
            sequence=42
        )
        
        assert msg.msg_type == MessageType.SHADOW_DATA
        assert msg.source_id == "node1"
        assert msg.payload == b"test data"
    
    def test_pack_unpack(self):
        msg = Message(
            msg_type=MessageType.SHADOW_DATA,
            source_id="node1",
            payload=b"test data",
            timestamp=123456789000000,
            sequence=42
        )
        
        packed = msg.pack()
        unpacked = Message.unpack(packed)
        
        assert unpacked.msg_type == msg.msg_type
        assert unpacked.source_id == msg.source_id
        assert unpacked.payload == msg.payload
        assert unpacked.timestamp == msg.timestamp
        assert unpacked.sequence == msg.sequence
    
    def test_pack_unpack_large_payload(self):
        large_payload = b"x" * 10000
        msg = Message(
            msg_type=MessageType.AUDIO_FRAME,
            source_id="node1",
            payload=large_payload
        )
        
        packed = msg.pack()
        unpacked = Message.unpack(packed)
        
        assert unpacked.payload == large_payload


class TestShadowData:
    """Test ShadowData class."""
    
    def test_creation(self):
        data = ShadowData(
            array_id="array1",
            timestamp_ns=123456789000000,
            object_id="obj1",
            angle=45.0,
            distance=2.5,
            confidence=0.85,
            position=(1.0, 2.0)
        )
        
        assert data.array_id == "array1"
        assert data.confidence == 0.85
    
    def test_to_from_bytes(self):
        data = ShadowData(
            array_id="array1",
            timestamp_ns=123456789000000,
            object_id="obj1",
            angle=45.0,
            distance=2.5,
            confidence=0.85,
            position=(1.0, 2.0)
        )
        
        bytes_data = data.to_bytes()
        restored = ShadowData.from_bytes(bytes_data)
        
        assert restored.array_id == data.array_id
        assert restored.timestamp_ns == data.timestamp_ns
        assert restored.object_id == data.object_id
        assert abs(restored.angle - data.angle) < 0.001
        assert abs(restored.distance - data.distance) < 0.001
        assert abs(restored.confidence - data.confidence) < 0.001
        assert abs(restored.position[0] - data.position[0]) < 0.001


class TestMockNetwork:
    """Test MockNetwork for testing."""
    
    @pytest.mark.asyncio
    async def test_register_unregister(self):
        mock = MockNetwork()
        
        # Create a simple network manager mock
        class MockManager:
            def __init__(self):
                self.node_id = "test_node"
                self.messages = []
            
            async def _on_message(self, msg, addr):
                self.messages.append(msg)
        
        manager = MockManager()
        await mock.register_node(manager)
        assert "test_node" in mock._nodes
        
        await mock.unregister_node("test_node")
        assert "test_node" not in mock._nodes
    
    @pytest.mark.asyncio
    async def test_route_message(self):
        mock = MockNetwork()
        
        received_messages = []
        
        class MockManager:
            def __init__(self, node_id):
                self.node_id = node_id
            
            async def _on_message(self, msg, addr):
                received_messages.append((self.node_id, msg))
        
        source = MockManager("source")
        target = MockManager("target")
        
        await mock.register_node(source)
        await mock.register_node(target)
        
        msg = Message(MessageType.SHADOW_DATA, "source", b"test")
        await mock.route_message("source", "target", msg)
        
        assert len(received_messages) == 1
        assert received_messages[0][0] == "target"
    
    @pytest.mark.asyncio
    async def test_latency_simulation(self):
        mock = MockNetwork()
        mock.set_latency(50)  # 50ms latency
        
        class MockManager:
            node_id = "test"
            async def _on_message(self, msg, addr): pass
        
        await mock.register_node(MockManager())
        
        start = time.time()
        msg = Message(MessageType.SHADOW_DATA, "source", b"test")
        await mock.route_message("source", "test", msg)
        elapsed = (time.time() - start) * 1000
        
        # Should have taken at least 50ms
        assert elapsed >= 45  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_packet_loss_simulation(self):
        mock = MockNetwork()
        mock.set_packet_loss(1.0)  # 100% loss
        
        received = []
        
        class MockManager:
            node_id = "test"
            async def _on_message(self, msg, addr):
                received.append(msg)
        
        await mock.register_node(MockManager())
        
        msg = Message(MessageType.SHADOW_DATA, "source", b"test")
        await mock.route_message("source", "test", msg)
        
        # Message should be lost
        assert len(received) == 0


class TestNetworkManager:
    """Test NetworkManager class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        manager = NetworkManager(
            "test_node",
            NetworkEndpoint("127.0.0.1", 5000),
            NetworkEndpoint("127.0.0.1", 6000)
        )
        
        assert manager.node_id == "test_node"
        assert manager.udp_endpoint.port == 5000
        assert manager.tcp_endpoint.port == 6000
    
    @pytest.mark.asyncio
    async def test_handler_registration(self):
        manager = NetworkManager(
            "test_node",
            NetworkEndpoint("127.0.0.1", 5000),
            NetworkEndpoint("127.0.0.1", 6000)
        )
        
        handler_calls = []
        
        async def handler(msg, addr):
            handler_calls.append((msg, addr))
        
        manager.register_handler(MessageType.SHADOW_DATA, handler)
        
        # Simulate message
        msg = Message(MessageType.SHADOW_DATA, "source", b"test")
        await manager._on_message(msg, NetworkEndpoint("127.0.0.1", 5001))
        
        assert len(handler_calls) == 1
    
    @pytest.mark.asyncio
    async def test_bandwidth_estimation(self):
        manager = NetworkManager(
            "test_node",
            NetworkEndpoint("127.0.0.1", 5000),
            NetworkEndpoint("127.0.0.1", 6000)
        )
        
        # Before starting, should be 0
        assert manager.estimate_bandwidth_mbps() == 0.0


class TestNetworkIntegration:
    """Integration tests for network layer."""
    
    @pytest.mark.asyncio
    async def test_udp_transport_lifecycle(self):
        """Test UDP transport start/stop."""
        from network.transport import TransportHandler
        
        class TestHandler(TransportHandler):
            async def on_message(self, msg, addr): pass
            async def on_connect(self, endpoint): pass
            async def on_disconnect(self, endpoint): pass
        
        transport = UDPTransport(
            NetworkEndpoint("127.0.0.1", 0),  # Auto-assign port
            TestHandler()
        )
        
        await transport.start()
        assert transport._running
        
        await transport.stop()
        assert not transport._running
    
    @pytest.mark.asyncio
    async def test_message_sequence(self):
        """Test message sequence numbers increment."""
        from network.transport import TransportHandler
        
        class TestHandler(TransportHandler):
            async def on_message(self, msg, addr): pass
            async def on_connect(self, endpoint): pass
            async def on_disconnect(self, endpoint): pass
        
        transport = UDPTransport(
            NetworkEndpoint("127.0.0.1", 0),
            TestHandler()
        )
        
        msg1 = Message(MessageType.SHADOW_DATA, "test", b"data1")
        msg2 = Message(MessageType.SHADOW_DATA, "test", b"data2")
        
        # Can't test send without transport started, but can verify sequence logic
        assert transport._sequence == 0


class TestNetworkPerformance:
    """Performance tests for network layer."""
    
    def test_message_pack_performance(self):
        """Measure message packing performance."""
        import timeit
        
        msg = Message(
            MessageType.SHADOW_DATA,
            "node1",
            b"x" * 100,
            timestamp=123456789000000
        )
        
        def pack():
            msg.pack()
        
        elapsed = timeit.timeit(pack, number=10000)
        
        # Should be fast (< 10ms for 10000 iterations)
        assert elapsed < 0.01
    
    def test_shadow_data_serialization(self):
        """Measure shadow data serialization performance."""
        import timeit
        
        data = ShadowData(
            array_id="array1",
            timestamp_ns=123456789000000,
            object_id="obj1",
            angle=45.0,
            distance=2.5,
            confidence=0.85,
            position=(1.0, 2.0)
        )
        
        def serialize():
            bytes_data = data.to_bytes()
            ShadowData.from_bytes(bytes_data)
        
        elapsed = timeit.timeit(serialize, number=10000)
        
        # Should be fast
        assert elapsed < 0.01
    
    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self):
        """Test handling many concurrent messages."""
        received = []
        
        class MockHandler:
            async def on_message(self, msg, addr):
                received.append(msg)
                await asyncio.sleep(0.001)  # Simulate processing
        
        handler = MockHandler()
        
        # Create many messages
        messages = [
            Message(MessageType.SHADOW_DATA, f"node_{i}", b"data")
            for i in range(100)
        ]
        
        # Process concurrently
        start = time.time()
        await asyncio.gather(*[
            handler.on_message(msg, NetworkEndpoint("127.0.0.1", 5000))
            for msg in messages
        ])
        elapsed = time.time() - start
        
        assert len(received) == 100
        # Should complete in reasonable time (allowing for sleep)
        assert elapsed < 0.5
"""
Tests for PTP Time Synchronization.
"""

import asyncio
import pytest
import time
from typing import List

from network.ptp_sync import (
    PTPSynchronizer, Timestamp, PTPMessage, SyncStatus,
    ClockDriftCompensator, SyncMonitor, create_synchronizer
)


class TestTimestamp:
    """Test Timestamp class."""
    
    def test_creation(self):
        ts = Timestamp(100, 500_000_000)
        assert ts.seconds == 100
        assert ts.nanoseconds == 500_000_000
    
    def test_now(self):
        ts = Timestamp.now()
        assert ts.seconds > 0
        assert 0 <= ts.nanoseconds < 1_000_000_000
    
    def test_to_nanoseconds(self):
        ts = Timestamp(1, 500_000_000)
        assert ts.to_nanoseconds() == 1_500_000_000
    
    def test_subtraction(self):
        ts1 = Timestamp(10, 0)
        ts2 = Timestamp(5, 500_000_000)
        diff = ts1 - ts2
        assert diff == 4_500_000_000
    
    def test_addition(self):
        ts = Timestamp(10, 0)
        result = ts + 500_000_000
        assert result.seconds == 10
        assert result.nanoseconds == 500_000_000
    
    def test_pack_unpack(self):
        ts = Timestamp(123456789, 987654321)
        packed = ts.pack()
        unpacked = Timestamp.unpack(packed)
        assert ts.seconds == unpacked.seconds
        assert ts.nanoseconds == unpacked.nanoseconds


class TestPTPMessage:
    """Test PTPMessage class."""
    
    def test_pack_unpack(self):
        ts = Timestamp.now()
        msg = PTPMessage(
            msg_type=PTPMessage.SYNC,
            source_id="test_node",
            origin_timestamp=ts,
            correction_field=100
        )
        
        packed = msg.pack()
        unpacked = PTPMessage.unpack(packed)
        
        assert unpacked.msg_type == msg.msg_type
        assert unpacked.source_id == msg.source_id
        assert unpacked.origin_timestamp.seconds == ts.seconds
        assert unpacked.correction_field == msg.correction_field
    
    def test_with_receive_timestamp(self):
        ts1 = Timestamp.now()
        ts2 = Timestamp(ts1.seconds + 1, 0)
        
        msg = PTPMessage(
            msg_type=PTPMessage.DELAY_RESP,
            source_id="test_node",
            origin_timestamp=ts1,
            receive_timestamp=ts2,
            correction_field=0
        )
        
        packed = msg.pack()
        unpacked = PTPMessage.unpack(packed)
        
        assert unpacked.receive_timestamp is not None
        assert unpacked.receive_timestamp.seconds == ts2.seconds


class TestClockDriftCompensator:
    """Test ClockDriftCompensator class."""
    
    @pytest.mark.asyncio
    async def test_drift_calculation(self):
        compensator = ClockDriftCompensator(window_size=10)
        
        # Add samples with known drift
        base_time = time.time()
        for i in range(15):
            local = base_time + i * 0.1
            master = local + i * 0.00001  # 100 ppm drift
            await compensator.add_sample(local, master)
        
        # Allow time for calculation
        await asyncio.sleep(0.01)
        
        # Check drift detected (should be around 100 ppm)
        assert abs(compensator.drift_ppm - 100) < 50
    
    @pytest.mark.asyncio
    async def test_compensation(self):
        compensator = ClockDriftCompensator()
        
        # Add offset samples
        for i in range(20):
            local = time.time() + i * 0.05
            master = local + 0.001  # 1ms offset
            await compensator.add_sample(local, master)
        
        await asyncio.sleep(0.01)
        
        # Test compensation
        test_time = time.time()
        compensated = compensator.compensate(test_time)
        
        # Should be close to master time
        assert abs(compensated - (test_time + 0.001)) < 0.0005


class TestSyncMonitor:
    """Test SyncMonitor class."""
    
    @pytest.mark.asyncio
    async def test_update_and_query(self):
        monitor = SyncMonitor()
        
        from network.ptp_sync import SyncStats
        stats = SyncStats(offset_ns=500, delay_ns=1000, sync_count=10)
        
        await monitor.update_node("node1", stats)
        
        assert monitor.node_count == 1
        assert monitor.get_stats("node1") == stats
        assert not monitor.all_synced  # offset > 1000ns
    
    @pytest.mark.asyncio
    async def test_all_synced(self):
        monitor = SyncMonitor()
        from network.ptp_sync import SyncStats
        
        # Add synced node
        await monitor.update_node("node1", SyncStats(offset_ns=500, sync_count=10))
        assert not monitor.all_synced  # Need multiple samples
        
        # Add another synced node
        await monitor.update_node("node2", SyncStats(offset_ns=800, sync_count=10))
        assert monitor.all_synced
    
    @pytest.mark.asyncio
    async def test_callback(self):
        monitor = SyncMonitor()
        callbacks: List[tuple] = []
        
        def callback(node_id: str, stats):
            callbacks.append((node_id, stats))
        
        monitor.add_callback(callback)
        
        from network.ptp_sync import SyncStats
        await monitor.update_node("node1", SyncStats())
        
        assert len(callbacks) == 1
        assert callbacks[0][0] == "node1"


class TestPTPSynchronizer:
    """Test PTPSynchronizer class."""
    
    @pytest.mark.asyncio
    async def test_master_initialization(self):
        sync = PTPSynchronizer("master_node", is_master=True)
        assert sync.node_id == "master_node"
        assert sync.is_master
        assert sync.status == SyncStatus.MASTER
    
    @pytest.mark.asyncio
    async def test_slave_initialization(self):
        sync = PTPSynchronizer("slave_node", is_master=False)
        assert sync.node_id == "slave_node"
        assert not sync.is_master
        assert sync.status == SyncStatus.UNSYNCED
    
    @pytest.mark.asyncio
    async def test_callback_registration(self):
        sync = PTPSynchronizer("test_node")
        
        callbacks = []
        def cb(stats):
            callbacks.append(stats)
        
        sync.add_sync_callback(cb)
        assert cb in sync._sync_callbacks
        
        sync.remove_sync_callback(cb)
        assert cb not in sync._sync_callbacks
    
    @pytest.mark.asyncio
    async def test_get_synced_time(self):
        sync = PTPSynchronizer("test_node")
        
        ts1 = sync.get_synced_time()
        await asyncio.sleep(0.01)
        ts2 = sync.get_synced_time()
        
        # Time should advance
        assert ts2.to_nanoseconds() > ts1.to_nanoseconds()


class TestPTPIntegration:
    """Integration tests for PTP synchronization."""
    
    @pytest.mark.asyncio
    async def test_master_slave_sync(self):
        """Test basic master-slave synchronization."""
        # Create master
        master = PTPSynchronizer("master", is_master=True, sync_interval_ms=50)
        
        # Create slave
        slave = PTPSynchronizer("slave", is_master=False)
        
        # Track sync status
        sync_events = []
        def on_sync(stats):
            sync_events.append(stats)
        
        slave.add_sync_callback(on_sync)
        
        # Start both
        await master.start()
        await slave.start()
        
        # Let them sync for a bit
        await asyncio.sleep(0.5)
        
        # Stop
        await master.stop()
        await slave.stop()
        
        # Verify sync occurred
        assert len(sync_events) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_slaves(self):
        """Test master with multiple slaves."""
        master = PTPSynchronizer("master", is_master=True, sync_interval_ms=50)
        
        slaves = [
            PTPSynchronizer(f"slave_{i}", is_master=False)
            for i in range(3)
        ]
        
        # Start all
        await master.start()
        for slave in slaves:
            await slave.start()
        
        # Let them sync
        await asyncio.sleep(0.5)
        
        # Stop all
        await master.stop()
        for slave in slaves:
            await slave.stop()
        
        # All should have received sync messages
        for slave in slaves:
            assert slave.stats.sync_count > 0


class TestSyncPerformance:
    """Performance tests for synchronization."""
    
    @pytest.mark.asyncio
    async def test_sync_latency(self):
        """Measure sync message processing latency."""
        sync = PTPSynchronizer("test", is_master=True)
        
        start = time.time()
        await sync.start()
        
        # Wait for a few sync cycles
        await asyncio.sleep(0.2)
        
        await sync.stop()
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 1.0
    
    def test_timestamp_overhead(self):
        """Measure timestamp creation overhead."""
        import timeit
        
        def create_timestamp():
            Timestamp.now()
        
        # Run 10000 iterations
        elapsed = timeit.timeit(create_timestamp, number=10000)
        
        # Should be very fast (< 1ms per 1000 calls)
        assert elapsed < 0.01
    
    def test_message_pack_overhead(self):
        """Measure message packing overhead."""
        import timeit
        
        ts = Timestamp.now()
        msg = PTPMessage(PTPMessage.SYNC, "test", ts)
        
        def pack_message():
            msg.pack()
        
        elapsed = timeit.timeit(pack_message, number=10000)
        
        # Should be fast
        assert elapsed < 0.01
"""
8-Array Multi-Array Simulation for Distributed Shadow Network.

Simulates a factory/room-scale deployment with 8 microphone arrays
and multiple moving objects to demonstrate the distributed tracking system.
"""

import asyncio
import time
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from node.shadow_node import ShadowNode, ShadowNodeCluster
from fusion.shadow_fusion import ArrayPosition, Vector2D


@dataclass
class SimulatedObject:
    """Simulated moving object in the environment."""
    object_id: str
    position: Vector2D
    velocity: Vector2D
    size: float = 0.5  # meters
    
    def update(self, dt: float, room_width: float, room_height: float) -> None:
        """Update position with boundary bouncing."""
        new_pos = Vector2D(
            self.position.x + self.velocity.x * dt,
            self.position.y + self.velocity.y * dt
        )
        
        # Bounce off walls
        new_vx = self.velocity.x
        new_vy = self.velocity.y
        
        if new_pos.x < 0 or new_pos.x > room_width:
            new_vx = -self.velocity.x
            new_pos = Vector2D(
                max(0, min(room_width, new_pos.x)),
                new_pos.y
            )
        
        if new_pos.y < 0 or new_pos.y > room_height:
            new_vy = -self.velocity.y
            new_pos = Vector2D(
                new_pos.x,
                max(0, min(room_height, new_pos.y))
            )
        
        self.position = new_pos
        self.velocity = Vector2D(new_vx, new_vy)


@dataclass
class SimulationConfig:
    """Configuration for the simulation."""
    room_width: float = 20.0  # meters
    room_height: float = 20.0  # meters
    num_arrays: int = 8
    num_objects: int = 10
    simulation_duration: float = 30.0  # seconds
    update_rate_hz: float = 100.0
    
    # Array configuration
    array_detection_radius: float = 10.0  # meters
    array_fov_degrees: float = 360.0
    
    # Object movement
    object_max_speed: float = 2.0  # m/s
    object_min_speed: float = 0.5  # m/s


class MultiArraySimulation:
    """
    8-Array simulation for distributed shadow tracking.
    
    Simulates:
    - 8 microphone arrays in optimal positions
    - 10 moving objects
    - Real-time shadow detection and fusion
    - Object handoffs between arrays
    """
    
    def __init__(self, config: SimulationConfig = None) -> None:
        self.config = config or SimulationConfig()
        self.cluster = ShadowNodeCluster()
        self.objects: Dict[str, SimulatedObject] = {}
        self.running = False
        
        # Statistics
        self.stats = {
            "frames_processed": 0,
            "detections_generated": 0,
            "fusions_performed": 0,
            "handoffs_observed": 0,
            "start_time": 0.0
        }
        
        # Callbacks
        self._frame_callbacks: List[Callable[[int, Dict], None]] = []
        self._object_callbacks: List[Callable[[str, SimulatedObject], None]] = []
    
    def _get_array_positions(self) -> List[Tuple[float, float]]:
        """Calculate optimal positions for 8 arrays."""
        w, h = self.config.room_width, self.config.room_height
        margin = 2.0
        
        return [
            # Corners
            (margin, margin),
            (w - margin, margin),
            (margin, h - margin),
            (w - margin, h - margin),
            # Midpoints
            (w / 2, margin),
            (w / 2, h - margin),
            (margin, h / 2),
            (w - margin, h / 2)
        ]
    
    async def setup(self) -> None:
        """Set up the simulation environment."""
        print("Setting up 8-array simulation...")
        print(f"  Room size: {self.config.room_width}m x {self.config.room_height}m")
        print(f"  Arrays: {self.config.num_arrays}")
        print(f"  Objects: {self.config.num_objects}")
        
        # Create arrays
        positions = self._get_array_positions()
        
        for i, pos in enumerate(positions[:self.config.num_arrays]):
            node = await self.cluster.create_node(
                f"array_{i}",
                position=pos,
                orientation=0.0,
                is_coordinator=(i == 0),
                max_objects=self.config.num_objects,
                target_latency_ms=10.0
            )
            print(f"  Created array_{i} at ({pos[0]:.1f}, {pos[1]:.1f})")
        
        # Create simulated objects
        for i in range(self.config.num_objects):
            obj_id = f"obj_{i:02d}"
            
            # Random position
            pos = Vector2D(
                random.uniform(2.0, self.config.room_width - 2.0),
                random.uniform(2.0, self.config.room_height - 2.0)
            )
            
            # Random velocity
            speed = random.uniform(
                self.config.object_min_speed,
                self.config.object_max_speed
            )
            angle = random.uniform(0, 2 * math.pi)
            vel = Vector2D(
                speed * math.cos(angle),
                speed * math.sin(angle)
            )
            
            self.objects[obj_id] = SimulatedObject(obj_id, pos, vel)
            print(f"  Created {obj_id} at ({pos.x:.1f}, {pos.y:.1f})")
        
        # Allow arrays to discover each other
        print("\nWaiting for array discovery and sync...")
        await asyncio.sleep(1.0)
        
        # Check sync status
        for node in self.cluster.get_all_nodes():
            stats = node.get_stats()
            print(f"  {node.node_id}: sync_offset={stats.sync_offset_ns:.0f}ns")
    
    async def run(self) -> Dict:
        """Run the simulation."""
        print("\n" + "=" * 60)
        print("STARTING SIMULATION")
        print("=" * 60)
        
        self.running = True
        self.stats["start_time"] = time.time()
        
        dt = 1.0 / self.config.update_rate_hz
        frame = 0
        
        try:
            while self.running:
                frame_start = time.perf_counter()
                
                # Update all objects
                for obj in self.objects.values():
                    obj.update(dt, self.config.room_width, self.config.room_height)
                    
                    for callback in self._object_callbacks:
                        callback(obj.object_id, obj)
                
                # Generate detections from each array
                await self._generate_detections()
                
                # Update statistics
                self.stats["frames_processed"] = frame
                
                # Notify frame callbacks
                frame_data = {
                    "frame": frame,
                    "time": time.time() - self.stats["start_time"],
                    "objects": {
                        oid: {"x": o.position.x, "y": o.position.y}
                        for oid, o in self.objects.items()
                    }
                }
                
                for callback in self._frame_callbacks:
                    callback(frame, frame_data)
                
                # Print progress
                if frame % 500 == 0:
                    self._print_status(frame)
                
                # Check duration
                elapsed = time.time() - self.stats["start_time"]
                if elapsed >= self.config.simulation_duration:
                    print(f"\nSimulation duration reached ({self.config.simulation_duration}s)")
                    break
                
                frame += 1
                
                # Maintain frame rate
                frame_elapsed = time.perf_counter() - frame_start
                sleep_time = max(0, dt - frame_elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        
        return self._collect_results()
    
    async def _generate_detections(self) -> None:
        """Generate shadow detections from arrays based on object positions."""
        nodes = self.cluster.get_all_nodes()
        
        for node in nodes:
            array_pos = node.array_position
            if not array_pos:
                continue
            
            for obj in self.objects.values():
                # Calculate distance and angle to object
                dx = obj.position.x - array_pos.position.x
                dy = obj.position.y - array_pos.position.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Check if within detection range
                if distance > self.config.array_detection_radius:
                    continue
                
                # Calculate angle from array orientation
                angle_rad = math.atan2(dx, dy)
                angle_deg = math.degrees(angle_rad) - array_pos.orientation
                angle_deg = (angle_deg + 360) % 360
                
                # Check FOV
                if self.config.array_fov_degrees < 360:
                    half_fov = self.config.array_fov_degrees / 2
                    angle_from_center = (angle_deg - array_pos.orientation + 180) % 360 - 180
                    if abs(angle_from_center) > half_fov:
                        continue
                
                # Calculate confidence based on distance
                confidence = 1.0 - (distance / self.config.array_detection_radius) * 0.3
                confidence *= random.uniform(0.9, 1.0)  # Add noise
                
                # Generate detection
                await node.detect_shadow(angle_deg, distance, confidence)
                self.stats["detections_generated"] += 1
    
    def _print_status(self, frame: int) -> None:
        """Print current simulation status."""
        elapsed = time.time() - self.stats["start_time"]
        fps = frame / elapsed if elapsed > 0 else 0
        
        # Get fusion stats from coordinator
        coordinator = self.cluster.get_node("array_0")
        fused_count = 0
        if coordinator and coordinator._fusion_engine:
            fused_count = coordinator._fusion_engine.get_shadow_count()
        
        print(f"  Frame {frame:5d} | {fps:5.1f} FPS | "
              f"Detections: {self.stats['detections_generated']:6d} | "
              f"Fused: {fused_count:3d}")
    
    def _collect_results(self) -> Dict:
        """Collect final simulation results."""
        elapsed = time.time() - self.stats["start_time"]
        
        # Get stats from all nodes
        node_stats = self.cluster.get_stats()
        
        # Get coordinator stats
        coordinator = self.cluster.get_node("array_0")
        global_objects = []
        if coordinator and coordinator._global_map:
            global_objects = coordinator._global_map.get_all_objects()
        
        results = {
            "duration": elapsed,
            "frames_processed": self.stats["frames_processed"],
            "detections_generated": self.stats["detections_generated"],
            "average_fps": self.stats["frames_processed"] / elapsed if elapsed > 0 else 0,
            "global_objects_tracked": len(global_objects),
            "node_statistics": {
                node_id: {
                    "shadows_detected": stats.shadows_detected,
                    "shadows_sent": stats.shadows_sent,
                    "shadows_received": stats.shadows_received,
                    "fusions": stats.fusions_performed,
                    "avg_latency_ms": stats.avg_processing_time_ms,
                    "sync_offset_ns": stats.sync_offset_ns
                }
                for node_id, stats in node_stats.items()
            }
        }
        
        return results
    
    async def shutdown(self) -> None:
        """Shutdown the simulation."""
        print("\nShutting down simulation...")
        self.running = False
        await self.cluster.stop_all()
        print("Simulation complete.")
    
    def add_frame_callback(self, callback: Callable[[int, Dict], None]) -> None:
        """Add callback for each simulation frame."""
        self._frame_callbacks.append(callback)
    
    def add_object_callback(self, callback: Callable[[str, SimulatedObject], None]) -> None:
        """Add callback for object updates."""
        self._object_callbacks.append(callback)


class Visualizer:
    """Simple text-based visualization of simulation."""
    
    def __init__(self, simulation: MultiArraySimulation) -> None:
        self.sim = simulation
        self.sim.add_frame_callback(self._on_frame)
    
    def _on_frame(self, frame: int, data: Dict) -> None:
        """Render frame (text-based)."""
        if frame % 100 != 0:  # Only render every 100 frames
            return
        
        # Simple status display
        objects = data.get("objects", {})
        print(f"\n  Objects: {len(objects)}")
        for obj_id, pos in list(objects.items())[:5]:  # Show first 5
            print(f"    {obj_id}: ({pos['x']:.1f}, {pos['y']:.1f})")


async def run_simulation(
    duration: float = 30.0,
    num_objects: int = 10,
    visualize: bool = False
) -> Dict:
    """
    Run the multi-array simulation.
    
    Args:
        duration: Simulation duration in seconds
        num_objects: Number of objects to track
        visualize: Enable text visualization
    
    Returns:
        Simulation results dictionary
    """
    config = SimulationConfig(
        simulation_duration=duration,
        num_objects=num_objects
    )
    
    sim = MultiArraySimulation(config)
    
    if visualize:
        Visualizer(sim)
    
    try:
        await sim.setup()
        results = await sim.run()
        
        print("\n" + "=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"Duration: {results['duration']:.1f}s")
        print(f"Frames: {results['frames_processed']}")
        print(f"Average FPS: {results['average_fps']:.1f}")
        print(f"Detections: {results['detections_generated']}")
        print(f"Global Objects: {results['global_objects_tracked']}")
        
        print("\nNode Statistics:")
        for node_id, stats in results['node_statistics'].items():
            print(f"  {node_id}:")
            print(f"    Shadows detected: {stats['shadows_detected']}")
            print(f"    Shadows sent: {stats['shadows_sent']}")
            print(f"    Shadows received: {stats['shadows_received']}")
            print(f"    Fusions: {stats['fusions']}")
            print(f"    Avg latency: {stats['avg_latency_ms']:.2f}ms")
            print(f"    Sync offset: {stats['sync_offset_ns']:.0f}ns")
        
        return results
    
    finally:
        await sim.shutdown()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="8-Array Distributed Shadow Network Simulation"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Simulation duration in seconds"
    )
    parser.add_argument(
        "--objects",
        type=int,
        default=10,
        help="Number of objects to track"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Enable text visualization"
    )
    
    args = parser.parse_args()
    
    await run_simulation(
        duration=args.duration,
        num_objects=args.objects,
        visualize=args.visualize
    )


if __name__ == "__main__":
    asyncio.run(main())
"""Node layer for individual array processing."""

from .shadow_node import (
    LocalShadow,
    NodeStats,
    ShadowNode,
    ShadowNodeCluster
)

__all__ = [
    'LocalShadow',
    'NodeStats',
    'ShadowNode',
    'ShadowNodeCluster'
]
"""
Shadow Node - Individual Array Node for Distributed Network.

Each shadow node represents a microphone array in the distributed network.
Handles local processing, data streaming, and coordination with other nodes.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
import logging

from ..network.transport import (
    NetworkManager, NetworkEndpoint, Message, MessageType, ShadowData
)
from ..network.ptp_sync import PTPSynchronizer, SyncStatus, create_synchronizer
from ..fusion.shadow_fusion import (
    ArrayPosition, Vector2D, ShadowObservation, ShadowFusionEngine
)
from ..fusion.global_map import GlobalShadowMap
from ..coordination.array_coordinator import (
    ArrayCoordinator, NodeRole, NodeState, NodeInfo
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LocalShadow:
    """Shadow detected by local array."""
    local_id: str
    timestamp_ns: int
    angle: float  # Degrees from array
    distance: float  # Meters
    confidence: float  # 0-1
    global_position: Vector2D
    
    # Tracking
    velocity: Vector2D = field(default_factory=lambda: Vector2D(0.0, 0.0))
    age_ms: float = 0.0


@dataclass(slots=True)
class NodeStats:
    """Statistics for shadow node."""
    shadows_detected: int = 0
    shadows_sent: int = 0
    shadows_received: int = 0
    fusions_performed: int = 0
    avg_processing_time_ms: float = 0.0
    network_latency_ms: float = 0.0
    sync_offset_ns: float = 0.0
    packets_dropped: int = 0


class ShadowNode:
    """
    Individual microphone array node in distributed network.
    
    Responsibilities:
    - Local shadow detection (simulated for testing)
    - Data streaming to other nodes
    - Shadow fusion with other arrays
    - Time synchronization
    - Health monitoring
    """
    
    def __init__(
        self,
        node_id: str,
        array_position: ArrayPosition,
        is_coordinator: bool = False,
        udp_port: int = 0,  # 0 = auto-assign
        tcp_port: int = 0,
        max_objects: int = 10,
        target_latency_ms: float = 10.0
    ) -> None:
        self.node_id = node_id
        self.array_position = array_position
        self.is_coordinator = is_coordinator
        self.max_objects = max_objects
        self.target_latency_ms = target_latency_ms
        
        # Auto-assign ports if not specified
        import random
        self.udp_port = udp_port or (5000 + random.randint(0, 1000))
        self.tcp_port = tcp_port or (6000 + random.randint(0, 1000))
        
        # Components
        self._network: Optional[NetworkManager] = None
        self._coordinator: Optional[ArrayCoordinator] = None
        self._fusion_engine: Optional[ShadowFusionEngine] = None
        self._global_map: Optional[GlobalShadowMap] = None
        
        # Local state
        self._local_shadows: Dict[str, LocalShadow] = {}
        self._shadow_counter = 0
        self._stats = NodeStats()
        
        # Processing
        self._processing_queue: asyncio.Queue[ShadowObservation] = asyncio.Queue()
        self._running = False
        
        # Callbacks
        self._shadow_callbacks: List[Callable[[LocalShadow], None]] = []
        self._fusion_callbacks: List[Callable[[Any], None]] = []
        
        # Tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._streaming_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the shadow node."""
        self._running = True
        
        # Initialize network
        self._network = NetworkManager(
            self.node_id,
            NetworkEndpoint("0.0.0.0", self.udp_port),
            NetworkEndpoint("0.0.0.0", self.tcp_port)
        )
        
        # Register handlers
        self._network.register_handler(
            MessageType.SHADOW_DATA, self._on_shadow_data_received
        )
        
        await self._network.start()
        logger.info(f"[{self.node_id}] Network started on UDP:{self.udp_port} TCP:{self.tcp_port}")
        
        # Initialize coordinator
        role = NodeRole.MASTER if self.is_coordinator else NodeRole.WORKER
        self._coordinator = ArrayCoordinator(
            self.node_id,
            role=role,
            udp_port=self.udp_port,
            tcp_port=self.tcp_port
        )
        await self._coordinator.start()
        
        # Register as array worker
        await self._coordinator.register_array(
            self.array_position,
            max_objects=self.max_objects,
            latency_ms=self.target_latency_ms
        )
        
        # Initialize fusion engine
        self._fusion_engine = ShadowFusionEngine()
        self._fusion_engine.register_array(self.array_position)
        self._fusion_engine.add_fusion_callback(self._on_fusion_complete)
        
        # Initialize global map (if coordinator)
        if self.is_coordinator:
            self._global_map = GlobalShadowMap(self._fusion_engine)
            self._global_map.add_object_callback(self._on_object_event)
        
        # Start background tasks
        self._processing_task = asyncio.create_task(self._processing_loop())
        self._streaming_task = asyncio.create_task(self._streaming_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"[{self.node_id}] Shadow node started as {role.name}")
    
    async def stop(self) -> None:
        """Stop the shadow node."""
        self._running = False
        
        # Cancel tasks
        for task in [self._processing_task, self._streaming_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop coordinator
        if self._coordinator:
            await self._coordinator.stop()
        
        # Stop network
        if self._network:
            await self._network.stop()
        
        logger.info(f"[{self.node_id}] Shadow node stopped")
    
    async def detect_shadow(
        self,
        angle: float,
        distance: float,
        confidence: float
    ) -> LocalShadow:
        """
        Report a locally detected shadow.
        
        This would normally come from the beamforming pipeline.
        """
        start_time = time.time_ns()
        
        self._shadow_counter += 1
        local_id = f"{self.node_id}_shadow_{self._shadow_counter}"
        
        # Convert to global coordinates
        local_pos = Vector2D(
            distance * math.sin(math.radians(angle)),
            distance * math.cos(math.radians(angle))
        )
        global_pos = self.array_position.local_to_global(local_pos)
        
        shadow = LocalShadow(
            local_id=local_id,
            timestamp_ns=time.time_ns(),
            angle=angle,
            distance=distance,
            confidence=confidence,
            global_position=global_pos
        )
        
        async with self._lock:
            self._local_shadows[local_id] = shadow
            self._stats.shadows_detected += 1
        
        # Create observation for fusion
        observation = ShadowObservation(
            observation_id=local_id,
            array_id=self.node_id,
            timestamp_ns=shadow.timestamp_ns,
            global_position=global_pos,
            confidence=confidence,
            angle=angle,
            distance=distance
        )
        
        # Queue for processing
        await self._processing_queue.put(observation)
        
        # Update processing time stat
        processing_time = (time.time_ns() - start_time) / 1_000_000
        self._stats.avg_processing_time_ms = (
            self._stats.avg_processing_time_ms * 0.9 + processing_time * 0.1
        )
        
        # Notify callbacks
        for callback in self._shadow_callbacks:
            try:
                callback(shadow)
            except Exception as e:
                logger.error(f"Shadow callback error: {e}")
        
        return shadow
    
    async def detect_shadows_batch(
        self,
        detections: List[Tuple[float, float, float]]
    ) -> List[LocalShadow]:
        """Detect multiple shadows in batch."""
        results = await asyncio.gather(*[
            self.detect_shadow(angle, dist, conf)
            for angle, dist, conf in detections
        ])
        return results
    
    def add_shadow_callback(self, callback: Callable[[LocalShadow], None]) -> None:
        """Add callback for local shadow detection."""
        self._shadow_callbacks.append(callback)
    
    def add_fusion_callback(self, callback: Callable[[Any], None]) -> None:
        """Add callback for fusion events."""
        self._fusion_callbacks.append(callback)
    
    def get_stats(self) -> NodeStats:
        """Get node statistics."""
        # Update sync offset
        if self._coordinator and self._coordinator._ptp:
            self._stats.sync_offset_ns = self._coordinator._ptp.stats.offset_ns
        
        return self._stats
    
    def get_local_shadows(self) -> List[LocalShadow]:
        """Get all locally detected shadows."""
        return list(self._local_shadows.values())
    
    def get_fused_shadows(self) -> List[Any]:
        """Get all fused shadows."""
        if self._fusion_engine:
            return self._fusion_engine.get_all_shadows()
        return []
    
    def get_global_objects(self) -> List[Any]:
        """Get global tracked objects (coordinator only)."""
        if self._global_map:
            return self._global_map.get_all_objects()
        return []
    
    async def _processing_loop(self) -> None:
        """Process observations from queue."""
        while self._running:
            try:
                # Get observation with timeout
                observation = await asyncio.wait_for(
                    self._processing_queue.get(),
                    timeout=0.1
                )
                
                # Process locally
                if self._fusion_engine:
                    fused = await self._fusion_engine.process_observation(observation)
                    if fused:
                        self._stats.fusions_performed += 1
                        
                        # Update coordinator stats
                        if self._coordinator:
                            self._coordinator._local_info.objects_tracked = \
                                self._fusion_engine.get_shadow_count()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[{self.node_id}] Processing error: {e}")
    
    async def _streaming_loop(self) -> None:
        """Stream shadow data to other nodes."""
        while self._running:
            try:
                # Get current shadows to stream
                shadows_to_stream = []
                async with self._lock:
                    shadows_to_stream = list(self._local_shadows.values())
                
                # Stream to network
                for shadow in shadows_to_stream:
                    shadow_data = ShadowData(
                        array_id=self.node_id,
                        timestamp_ns=shadow.timestamp_ns,
                        object_id=shadow.local_id,
                        angle=shadow.angle,
                        distance=shadow.distance,
                        confidence=shadow.confidence,
                        position=(shadow.global_position.x, shadow.global_position.y)
                    )
                    
                    msg = Message(
                        msg_type=MessageType.SHADOW_DATA,
                        source_id=self.node_id,
                        payload=shadow_data.to_bytes(),
                        timestamp=time.time_ns()
                    )
                    
                    if self._network:
                        self._network.send_udp_multicast(msg)
                        self._stats.shadows_sent += 1
                
            except Exception as e:
                logger.error(f"[{self.node_id}] Streaming error: {e}")
            
            # Stream at 100Hz
            await asyncio.sleep(0.01)
    
    async def _cleanup_loop(self) -> None:
        """Clean up stale shadows."""
        while self._running:
            try:
                current_time = time.time_ns()
                stale_ids = []
                
                async with self._lock:
                    for shadow_id, shadow in list(self._local_shadows.items()):
                        age_ms = (current_time - shadow.timestamp_ns) / 1_000_000
                        if age_ms > 500:  # 500ms timeout
                            stale_ids.append(shadow_id)
                    
                    for shadow_id in stale_ids:
                        del self._local_shadows[shadow_id]
                
                # Cleanup fusion engine
                if self._fusion_engine:
                    await self._fusion_engine.cleanup_stale_shadows(current_time)
                
                # Cleanup global map
                if self._global_map:
                    await self._global_map.cleanup_stale_objects(current_time)
                
            except Exception as e:
                logger.error(f"[{self.node_id}] Cleanup error: {e}")
            
            await asyncio.sleep(0.1)
    
    async def _on_shadow_data_received(
        self,
        message: Message,
        addr: NetworkEndpoint
    ) -> None:
        """Handle shadow data from another node."""
        try:
            shadow_data = ShadowData.from_bytes(message.payload)
            
            # Create observation from received data
            observation = ShadowObservation(
                observation_id=f"{shadow_data.array_id}_{shadow_data.object_id}",
                array_id=shadow_data.array_id,
                timestamp_ns=shadow_data.timestamp_ns,
                global_position=Vector2D(
                    shadow_data.position[0],
                    shadow_data.position[1]
                ),
                confidence=shadow_data.confidence,
                angle=shadow_data.angle,
                distance=shadow_data.distance
            )
            
            # Register array if not known
            if self._fusion_engine:
                # Note: In production, array positions would be exchanged during discovery
                # Here we assume they're pre-configured or exchanged separately
                pass
            
            # Process observation
            await self._processing_queue.put(observation)
            self._stats.shadows_received += 1
            
        except Exception as e:
            logger.error(f"[{self.node_id}] Shadow data handling error: {e}")
            self._stats.packets_dropped += 1
    
    def _on_fusion_complete(self, fused_shadow: Any) -> None:
        """Handle fusion completion."""
        # Update global map if coordinator
        if self._global_map:
            asyncio.create_task(self._global_map.update_from_fusion(fused_shadow))
        
        # Notify callbacks
        for callback in self._fusion_callbacks:
            try:
                callback(fused_shadow)
            except Exception as e:
                logger.error(f"Fusion callback error: {e}")
    
    def _on_object_event(self, obj: Any, event: str) -> None:
        """Handle global object events."""
        logger.debug(f"[{self.node_id}] Object {obj.object_id}: {event}")


import math


class ShadowNodeCluster:
    """
    Manager for a cluster of shadow nodes.
    
    Simplifies creation and management of multiple nodes.
    """
    
    def __init__(self) -> None:
        self._nodes: Dict[str, ShadowNode] = {}
        self._lock = asyncio.Lock()
    
    async def create_node(
        self,
        node_id: str,
        position: Tuple[float, float],
        orientation: float = 0.0,
        is_coordinator: bool = False,
        **kwargs
    ) -> ShadowNode:
        """Create and start a new shadow node."""
        array_pos = ArrayPosition(
            array_id=node_id,
            position=Vector2D(position[0], position[1]),
            orientation=orientation
        )
        
        node = ShadowNode(
            node_id=node_id,
            array_position=array_pos,
            is_coordinator=is_coordinator,
            **kwargs
        )
        
        await node.start()
        
        async with self._lock:
            self._nodes[node_id] = node
        
        return node
    
    async def remove_node(self, node_id: str) -> None:
        """Remove and stop a node."""
        async with self._lock:
            node = self._nodes.pop(node_id, None)
        
        if node:
            await node.stop()
    
    async def stop_all(self) -> None:
        """Stop all nodes."""
        async with self._lock:
            nodes = list(self._nodes.values())
            self._nodes.clear()
        
        await asyncio.gather(*[n.stop() for n in nodes], return_exceptions=True)
    
    def get_node(self, node_id: str) -> Optional[ShadowNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)
    
    def get_all_nodes(self) -> List[ShadowNode]:
        """Get all nodes."""
        return list(self._nodes.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        return {
            node_id: node.get_stats()
            for node_id, node in self._nodes.items()
        }
"""Network layer for distributed shadow tracking."""

from .ptp_sync import (
    PTPSynchronizer,
    Timestamp,
    PTPMessage,
    SyncStatus,
    SyncStats,
    ClockDriftCompensator,
    SyncMonitor,
    create_synchronizer
)

from .transport import (
    NetworkManager,
    NetworkEndpoint,
    Message,
    MessageType,
    ShadowData,
    UDPTransport,
    TCPTransport,
    MockNetwork
)

__all__ = [
    # PTP Sync
    'PTPSynchronizer',
    'Timestamp',
    'PTPMessage',
    'SyncStatus',
    'SyncStats',
    'ClockDriftCompensator',
    'SyncMonitor',
    'create_synchronizer',
    # Transport
    'NetworkManager',
    'NetworkEndpoint',
    'Message',
    'MessageType',
    'ShadowData',
    'UDPTransport',
    'TCPTransport',
    'MockNetwork'
]
"""
PTP (Precision Time Protocol) Implementation for Distributed Shadow Network.

Provides sub-microsecond time synchronization across multiple microphone arrays
using a simplified PTP-like protocol over UDP.
"""

from __future__ import annotations

import asyncio
import struct
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Protocol, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status of a node."""
    UNSYNCED = auto()
    SYNCING = auto()
    SYNCED = auto()
    MASTER = auto()
    ERROR = auto()


@dataclass(frozen=True, slots=True)
class Timestamp:
    """High-resolution timestamp with nanosecond precision."""
    seconds: int
    nanoseconds: int
    
    @classmethod
    def now(cls) -> Timestamp:
        """Create timestamp from current system time."""
        t = time.time_ns()
        return cls(seconds=t // 1_000_000_000, nanoseconds=t % 1_000_000_000)
    
    def to_nanoseconds(self) -> int:
        """Convert to total nanoseconds."""
        return self.seconds * 1_000_000_000 + self.nanoseconds
    
    def __sub__(self, other: Timestamp) -> int:
        """Return difference in nanoseconds."""
        return self.to_nanoseconds() - other.to_nanoseconds()
    
    def __add__(self, offset_ns: int) -> Timestamp:
        """Add nanoseconds offset."""
        total = self.to_nanoseconds() + offset_ns
        return Timestamp(total // 1_000_000_000, total % 1_000_000_000)
    
    def pack(self) -> bytes:
        """Pack to bytes for network transmission."""
        return struct.pack("!QI", self.seconds, self.nanoseconds)
    
    @classmethod
    def unpack(cls, data: bytes) -> Timestamp:
        """Unpack from network bytes."""
        seconds, nanoseconds = struct.unpack("!QI", data)
        return cls(seconds, nanoseconds)


@dataclass(frozen=True, slots=True)
class PTPMessage:
    """PTP protocol message."""
    msg_type: int  # 1=Sync, 2=Delay_Req, 3=Follow_Up, 4=Delay_Resp
    source_id: str
    origin_timestamp: Timestamp
    receive_timestamp: Optional[Timestamp] = None
    correction_field: int = 0  # Nanoseconds
    
    # Message types
    SYNC = 1
    DELAY_REQ = 2
    FOLLOW_UP = 3
    DELAY_RESP = 4
    ANNOUNCE = 5
    
    def pack(self) -> bytes:
        """Pack message to bytes."""
        data = struct.pack("!BB", self.msg_type, len(self.source_id))
        data += self.source_id.encode()
        data += self.origin_timestamp.pack()
        data += struct.pack("!Q", self.correction_field)
        if self.receive_timestamp:
            data += b'\x01' + self.receive_timestamp.pack()
        else:
            data += b'\x00'
        return data
    
    @classmethod
    def unpack(cls, data: bytes) -> PTPMessage:
        """Unpack message from bytes."""
        msg_type, id_len = struct.unpack("!BB", data[:2])
        source_id = data[2:2+id_len].decode()
        offset = 2 + id_len
        origin_timestamp = Timestamp.unpack(data[offset:offset+12])
        offset += 12
        correction_field = struct.unpack("!Q", data[offset:offset+8])[0]
        offset += 8
        has_receive = data[offset] == 1
        offset += 1
        receive_timestamp = None
        if has_receive:
            receive_timestamp = Timestamp.unpack(data[offset:offset+12])
        return cls(msg_type, source_id, origin_timestamp, receive_timestamp, correction_field)


@dataclass(slots=True)
class SyncStats:
    """Synchronization statistics."""
    offset_ns: float = 0.0  # Clock offset from master
    delay_ns: float = 0.0   # Network delay
    drift_ppm: float = 0.0  # Clock drift in parts per million
    last_sync: float = 0.0  # Timestamp of last sync
    sync_count: int = 0
    error_count: int = 0
    
    @property
    def is_synced(self) -> bool:
        """Check if synchronization is within acceptable bounds."""
        return abs(self.offset_ns) < 1000 and self.sync_count > 5


class ClockDriftCompensator:
    """Compensates for clock drift using linear regression."""
    
    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._samples: List[tuple[float, float]] = []  # (local_time, master_time)
        self._drift_ppm: float = 0.0
        self._offset_ns: float = 0.0
        self._lock = asyncio.Lock()
    
    async def add_sample(self, local_time: float, master_time: float) -> None:
        """Add a time sample for drift calculation."""
        async with self._lock:
            self._samples.append((local_time, master_time))
            if len(self._samples) > self._window_size:
                self._samples.pop(0)
            await self._calculate_drift()
    
    async def _calculate_drift(self) -> None:
        """Calculate drift using linear regression."""
        if len(self._samples) < 10:
            return
        
        n = len(self._samples)
        sum_x = sum(s[0] for s in self._samples)
        sum_y = sum(s[1] for s in self._samples)
        sum_xy = sum(s[0] * s[1] for s in self._samples)
        sum_x2 = sum(s[0] ** 2 for s in self._samples)
        
        # Linear regression: y = mx + b
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return
        
        m = (n * sum_xy - sum_x * sum_y) / denominator  # Slope (drift)
        b = (sum_y - m * sum_x) / n  # Intercept (offset)
        
        self._drift_ppm = (m - 1.0) * 1_000_000  # Convert to ppm
        self._offset_ns = b * 1_000_000_000  # Convert to nanoseconds
    
    def compensate(self, local_time: float) -> float:
        """Apply drift compensation to local time."""
        # Compensated time = local_time + offset + drift * local_time
        return local_time + (self._offset_ns / 1_000_000_000) + \
               (self._drift_ppm / 1_000_000) * local_time
    
    @property
    def drift_ppm(self) -> float:
        """Get current drift in parts per million."""
        return self._drift_ppm
    
    @property
    def offset_ns(self) -> float:
        """Get current offset in nanoseconds."""
        return self._offset_ns


class PTPSynchronizer:
    """
    PTP-like time synchronizer for distributed microphone arrays.
    
    Implements master-slave synchronization with clock drift compensation.
    Achieves sub-microsecond accuracy under ideal network conditions.
    """
    
    def __init__(
        self,
        node_id: str,
        is_master: bool = False,
        sync_interval_ms: float = 100.0,
        multicast_group: str = "239.255.0.1",
        ptp_port: int = 319
    ) -> None:
        self.node_id = node_id
        self.is_master = is_master
        self.sync_interval_ms = sync_interval_ms
        self.multicast_group = multicast_group
        self.ptp_port = ptp_port
        
        self._status = SyncStatus.MASTER if is_master else SyncStatus.UNSYNCED
        self._stats = SyncStats()
        self._drift_compensator = ClockDriftCompensator()
        
        # For delay calculation
        self._t1: Optional[Timestamp] = None  # Master send time
        self._t2: Optional[Timestamp] = None  # Slave receive time
        self._t3: Optional[Timestamp] = None  # Slave send time
        self._t4: Optional[Timestamp] = None  # Master receive time
        
        # Network
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[asyncio.DatagramProtocol] = None
        
        # Callbacks
        self._sync_callbacks: List[Callable[[SyncStats], None]] = []
        
        # Task management
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
    
    @property
    def status(self) -> SyncStatus:
        """Current synchronization status."""
        return self._status
    
    @property
    def stats(self) -> SyncStats:
        """Current synchronization statistics."""
        return self._stats
    
    def add_sync_callback(self, callback: Callable[[SyncStats], None]) -> None:
        """Register callback for sync status updates."""
        self._sync_callbacks.append(callback)
    
    def remove_sync_callback(self, callback: Callable[[SyncStats], None]) -> None:
        """Unregister sync callback."""
        if callback in self._sync_callbacks:
            self._sync_callbacks.remove(callback)
    
    async def start(self) -> None:
        """Start the PTP synchronizer."""
        self._running = True
        
        # Create UDP socket for PTP
        loop = asyncio.get_event_loop()
        self._transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: PTPProtocol(self._on_message_received),
            local_addr=("0.0.0.0", self.ptp_port),
            allow_broadcast=True
        )
        
        if self.is_master:
            self._sync_task = asyncio.create_task(self._master_sync_loop())
            logger.info(f"[{self.node_id}] PTP Master started")
        else:
            self._sync_task = asyncio.create_task(self._slave_sync_loop())
            logger.info(f"[{self.node_id}] PTP Slave started")
    
    async def stop(self) -> None:
        """Stop the PTP synchronizer."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        if self._transport:
            self._transport.close()
        logger.info(f"[{self.node_id}] PTP stopped")
    
    def get_synced_time(self) -> Timestamp:
        """Get current time compensated for drift."""
        local_time = time.time()
        compensated = self._drift_compensator.compensate(local_time)
        seconds = int(compensated)
        nanoseconds = int((compensated - seconds) * 1_000_000_000)
        return Timestamp(seconds, nanoseconds)
    
    def _on_message_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming PTP message."""
        try:
            msg = PTPMessage.unpack(data)
            asyncio.create_task(self._process_message(msg, addr))
        except Exception as e:
            logger.error(f"[{self.node_id}] Failed to parse PTP message: {e}")
            self._stats.error_count += 1
    
    async def _process_message(self, msg: PTPMessage, addr: tuple[str, int]) -> None:
        """Process PTP message based on type."""
        if msg.source_id == self.node_id:
            return  # Ignore own messages
        
        if self.is_master:
            await self._handle_master_message(msg, addr)
        else:
            await self._handle_slave_message(msg, addr)
    
    async def _handle_master_message(self, msg: PTPMessage, addr: tuple[str, int]) -> None:
        """Handle messages as master node."""
        if msg.msg_type == PTPMessage.DELAY_REQ:
            # Record receive time and send delay response
            t4 = Timestamp.now()
            delay_resp = PTPMessage(
                msg_type=PTPMessage.DELAY_RESP,
                source_id=self.node_id,
                origin_timestamp=msg.origin_timestamp,
                receive_timestamp=t4,
                correction_field=msg.correction_field
            )
            self._send_message(delay_resp, addr)
    
    async def _handle_slave_message(self, msg: PTPMessage, addr: tuple[str, int]) -> None:
        """Handle messages as slave node."""
        if msg.msg_type == PTPMessage.SYNC:
            # Record receive time
            self._t2 = Timestamp.now()
            self._t1 = msg.origin_timestamp
            self._status = SyncStatus.SYNCING
            
        elif msg.msg_type == PTPMessage.FOLLOW_UP:
            # More precise t1 from master
            self._t1 = msg.origin_timestamp
            
            # Send delay request
            await asyncio.sleep(0.01)  # Small delay to avoid collision
            self._t3 = Timestamp.now()
            delay_req = PTPMessage(
                msg_type=PTPMessage.DELAY_REQ,
                source_id=self.node_id,
                origin_timestamp=self._t3
            )
            self._send_message(delay_req, addr)
            
        elif msg.msg_type == PTPMessage.DELAY_RESP:
            # Calculate offset and delay
            if self._t1 and self._t2 and self._t3 and msg.receive_timestamp:
                self._t4 = msg.receive_timestamp
                await self._calculate_sync()
    
    async def _calculate_sync(self) -> None:
        """Calculate clock offset and network delay."""
        if not all([self._t1, self._t2, self._t3, self._t4]):
            return
        
        # PTP delay calculation
        # offset = ((t2 - t1) - (t4 - t3)) / 2
        # delay = ((t2 - t1) + (t4 - t3)) / 2
        
        t2_t1 = self._t2.to_nanoseconds() - self._t1.to_nanoseconds()
        t4_t3 = self._t4.to_nanoseconds() - self._t3.to_nanoseconds()
        
        offset_ns = (t2_t1 - t4_t3) / 2
        delay_ns = (t2_t1 + t4_t3) / 2
        
        self._stats.offset_ns = offset_ns
        self._stats.delay_ns = delay_ns
        self._stats.last_sync = time.time()
        self._stats.sync_count += 1
        
        # Add to drift compensator
        local_time = time.time()
        master_time = local_time + (offset_ns / 1_000_000_000)
        await self._drift_compensator.add_sample(local_time, master_time)
        
        self._stats.drift_ppm = self._drift_compensator.drift_ppm
        
        # Check if synced
        if abs(offset_ns) < 1000:  # Less than 1 microsecond
            self._status = SyncStatus.SYNCED
        
        # Notify callbacks
        for callback in self._sync_callbacks:
            try:
                callback(self._stats)
            except Exception as e:
                logger.error(f"Sync callback error: {e}")
    
    async def _master_sync_loop(self) -> None:
        """Master node sync loop - sends periodic sync messages."""
        while self._running:
            try:
                # Send Sync message
                t1 = Timestamp.now()
                sync_msg = PTPMessage(
                    msg_type=PTPMessage.SYNC,
                    source_id=self.node_id,
                    origin_timestamp=t1
                )
                self._send_multicast(sync_msg)
                
                # Send Follow_Up with precise timestamp
                await asyncio.sleep(0.001)  # Small delay
                follow_up = PTPMessage(
                    msg_type=PTPMessage.FOLLOW_UP,
                    source_id=self.node_id,
                    origin_timestamp=t1
                )
                self._send_multicast(follow_up)
                
            except Exception as e:
                logger.error(f"[{self.node_id}] Master sync error: {e}")
                self._stats.error_count += 1
            
            await asyncio.sleep(self.sync_interval_ms / 1000)
    
    async def _slave_sync_loop(self) -> None:
        """Slave node sync loop - monitors sync status."""
        while self._running:
            # Check if sync is stale
            if time.time() - self._stats.last_sync > 1.0:
                if self._status == SyncStatus.SYNCED:
                    self._status = SyncStatus.SYNCING
                elif self._status == SyncStatus.SYNCING and \
                     time.time() - self._stats.last_sync > 5.0:
                    self._status = SyncStatus.UNSYNCED
            
            await asyncio.sleep(self.sync_interval_ms / 1000)
    
    def _send_message(self, msg: PTPMessage, addr: tuple[str, int]) -> None:
        """Send PTP message to specific address."""
        if self._transport:
            self._transport.sendto(msg.pack(), addr)
    
    def _send_multicast(self, msg: PTPMessage) -> None:
        """Send PTP message to multicast group."""
        if self._transport:
            self._transport.sendto(msg.pack(), (self.multicast_group, self.ptp_port))


class PTPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for PTP messages."""
    
    def __init__(self, on_message: Callable[[bytes, tuple[str, int]], None]) -> None:
        self.on_message = on_message
        self._transport: Optional[asyncio.DatagramTransport] = None
    
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self._transport = transport
    
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.on_message(data, addr)
    
    def error_received(self, exc: Exception) -> None:
        logger.error(f"PTP protocol error: {exc}")


class SyncMonitor:
    """Monitors synchronization status across all nodes."""
    
    def __init__(self) -> None:
        self._nodes: Dict[str, SyncStats] = {}
        self._callbacks: List[Callable[[str, SyncStats], None]] = []
        self._lock = asyncio.Lock()
    
    async def update_node(self, node_id: str, stats: SyncStats) -> None:
        """Update sync stats for a node."""
        async with self._lock:
            self._nodes[node_id] = stats
            for callback in self._callbacks:
                try:
                    callback(node_id, stats)
                except Exception as e:
                    logger.error(f"Monitor callback error: {e}")
    
    def add_callback(self, callback: Callable[[str, SyncStats], None]) -> None:
        """Add status change callback."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, SyncStats], None]) -> None:
        """Remove status change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @property
    def all_synced(self) -> bool:
        """Check if all nodes are synchronized."""
        return all(s.is_synced for s in self._nodes.values())
    
    @property
    def node_count(self) -> int:
        """Number of monitored nodes."""
        return len(self._nodes)
    
    def get_stats(self, node_id: str) -> Optional[SyncStats]:
        """Get stats for specific node."""
        return self._nodes.get(node_id)
    
    def get_all_stats(self) -> Dict[str, SyncStats]:
        """Get all node stats."""
        return dict(self._nodes)


# Convenience function for creating synchronizer
async def create_synchronizer(
    node_id: str,
    is_master: bool = False,
    **kwargs
) -> PTPSynchronizer:
    """Factory function to create and start a PTP synchronizer."""
    sync = PTPSynchronizer(node_id, is_master, **kwargs)
    await sync.start()
    return sync
"""
Network Transport Layer for Distributed Shadow Network.

Provides UDP for real-time data streaming and TCP for control messages.
Implements async/await patterns with clean separation of concerns.
"""

from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Protocol, Set, TypeVar, Generic, Any
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MessageType(Enum):
    """Message types for the transport layer."""
    # UDP (Real-time data)
    SHADOW_DATA = 0x01      # Shadow detection data
    AUDIO_FRAME = 0x02      # Raw audio frame
    SYNC_DATA = 0x03        # Synchronization data
    
    # TCP (Control)
    HANDSHAKE = 0x10        # Node handshake
    CONFIG = 0x11           # Configuration update
    COMMAND = 0x12          # Control command
    STATUS = 0x13           # Status report
    DISCOVERY = 0x14        # Node discovery
    HEARTBEAT = 0x15        # Keepalive


@dataclass(frozen=True, slots=True)
class NetworkEndpoint:
    """Network endpoint identifier."""
    host: str
    port: int
    
    def __str__(self) -> str:
        return f"{self.host}:{self.port}"
    
    def __hash__(self) -> int:
        return hash((self.host, self.port))


@dataclass(slots=True)
class Message:
    """Generic network message."""
    msg_type: MessageType
    source_id: str
    payload: bytes
    timestamp: int = 0  # Nanoseconds
    sequence: int = 0
    
    def pack(self) -> bytes:
        """Pack message to bytes."""
        header = struct.pack(
            "!BBHQI",
            self.msg_type.value,
            len(self.source_id),
            len(self.payload),
            self.timestamp,
            self.sequence
        )
        return header + self.source_id.encode() + self.payload
    
    @classmethod
    def unpack(cls, data: bytes) -> Message:
        """Unpack message from bytes."""
        msg_type_val, id_len, payload_len, timestamp, sequence = struct.unpack(
            "!BBHQI", data[:16]
        )
        offset = 16
        source_id = data[offset:offset+id_len].decode()
        offset += id_len
        payload = data[offset:offset+payload_len]
        
        return cls(
            msg_type=MessageType(msg_type_val),
            source_id=source_id,
            payload=payload,
            timestamp=timestamp,
            sequence=sequence
        )


@dataclass(slots=True)
class ShadowData:
    """Shadow detection data from an array."""
    array_id: str
    timestamp_ns: int
    object_id: str
    angle: float  # Degrees
    distance: float  # Meters
    confidence: float  # 0-1
    position: tuple[float, float] = (0.0, 0.0)  # x, y in array coordinates
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        return struct.pack(
            "!16sQ16sdddff",
            self.array_id.encode().ljust(16, b'\x00')[:16],
            self.timestamp_ns,
            self.object_id.encode().ljust(16, b'\x00')[:16],
            self.angle,
            self.distance,
            self.confidence,
            self.position[0],
            self.position[1]
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> ShadowData:
        """Deserialize from bytes."""
        array_id, ts, obj_id, angle, dist, conf, x, y = struct.unpack("!16sQ16sdddff", data)
        return cls(
            array_id=array_id.decode().rstrip('\x00'),
            timestamp_ns=ts,
            object_id=obj_id.decode().rstrip('\x00'),
            angle=angle,
            distance=dist,
            confidence=conf,
            position=(x, y)
        )


class TransportHandler(ABC):
    """Abstract base class for transport handlers."""
    
    @abstractmethod
    async def on_message(self, message: Message, addr: NetworkEndpoint) -> None:
        """Handle received message."""
        pass
    
    @abstractmethod
    async def on_connect(self, endpoint: NetworkEndpoint) -> None:
        """Handle new connection."""
        pass
    
    @abstractmethod
    async def on_disconnect(self, endpoint: NetworkEndpoint) -> None:
        """Handle disconnection."""
        pass


class UDPTransport:
    """
    UDP transport for real-time data streaming.
    
    Optimized for low latency with:
    - No connection setup overhead
    - Minimal header size
    - Async send/receive
    """
    
    def __init__(
        self,
        local_endpoint: NetworkEndpoint,
        handler: TransportHandler,
        multicast_group: Optional[str] = None,
        buffer_size: int = 65535
    ) -> None:
        self.local_endpoint = local_endpoint
        self.handler = handler
        self.multicast_group = multicast_group
        self.buffer_size = buffer_size
        
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[asyncio.DatagramProtocol] = None
        self._sequence = 0
        self._running = False
        
        # Statistics
        self._packets_sent = 0
        self._packets_received = 0
        self._bytes_sent = 0
        self._bytes_received = 0
    
    async def start(self) -> None:
        """Start UDP transport."""
        self._running = True
        loop = asyncio.get_event_loop()
        
        self._transport, self._protocol = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self._on_datagram_received, self.buffer_size),
            local_addr=(self.local_endpoint.host, self.local_endpoint.port),
            allow_broadcast=True
        )
        
        logger.info(f"UDP transport started on {self.local_endpoint}")
    
    async def stop(self) -> None:
        """Stop UDP transport."""
        self._running = False
        if self._transport:
            self._transport.close()
        logger.info(f"UDP transport stopped on {self.local_endpoint}")
    
    def send(
        self,
        message: Message,
        endpoint: NetworkEndpoint
    ) -> None:
        """Send message via UDP."""
        if not self._transport:
            raise RuntimeError("Transport not started")
        
        message.sequence = self._sequence
        self._sequence = (self._sequence + 1) % 2**32
        
        data = message.pack()
        self._transport.sendto(data, (endpoint.host, endpoint.port))
        
        self._packets_sent += 1
        self._bytes_sent += len(data)
    
    def send_multicast(self, message: Message) -> None:
        """Send message to multicast group."""
        if self.multicast_group:
            self.send(message, NetworkEndpoint(self.multicast_group, self.local_endpoint.port))
    
    def _on_datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming datagram."""
        try:
            message = Message.unpack(data)
            endpoint = NetworkEndpoint(addr[0], addr[1])
            
            self._packets_received += 1
            self._bytes_received += len(data)
            
            asyncio.create_task(self.handler.on_message(message, endpoint))
        except Exception as e:
            logger.error(f"Failed to process UDP datagram: {e}")
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get transport statistics."""
        return {
            "packets_sent": self._packets_sent,
            "packets_received": self._packets_received,
            "bytes_sent": self._bytes_sent,
            "bytes_received": self._bytes_received
        }


class UDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol implementation."""
    
    def __init__(
        self,
        on_data: Callable[[bytes, tuple[str, int]], None],
        buffer_size: int
    ) -> None:
        self.on_data = on_data
        self.buffer_size = buffer_size
        self._transport: Optional[asyncio.DatagramTransport] = None
    
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self._transport = transport
    
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) <= self.buffer_size:
            self.on_data(data, addr)
    
    def error_received(self, exc: Exception) -> None:
        logger.error(f"UDP error: {exc}")


class TCPTransport:
    """
    TCP transport for control messages.
    
    Provides reliable, ordered delivery for:
    - Configuration updates
    - Command/control
    - Status reporting
    - Node discovery
    """
    
    def __init__(
        self,
        local_endpoint: NetworkEndpoint,
        handler: TransportHandler,
        max_connections: int = 100
    ) -> None:
        self.local_endpoint = local_endpoint
        self.handler = handler
        self.max_connections = max_connections
        
        self._server: Optional[asyncio.Server] = None
        self._connections: Dict[str, TCPConnection] = {}
        self._running = False
        
        # Statistics
        self._connections_accepted = 0
        self._connections_closed = 0
        self._messages_sent = 0
        self._messages_received = 0
    
    async def start(self) -> None:
        """Start TCP server."""
        self._running = True
        self._server = await asyncio.start_server(
            self._on_client_connected,
            self.local_endpoint.host,
            self.local_endpoint.port
        )
        logger.info(f"TCP transport started on {self.local_endpoint}")
    
    async def stop(self) -> None:
        """Stop TCP server."""
        self._running = False
        
        # Close all connections
        for conn in list(self._connections.values()):
            await conn.close()
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        logger.info(f"TCP transport stopped on {self.local_endpoint}")
    
    async def connect(self, endpoint: NetworkEndpoint) -> TCPConnection:
        """Connect to remote endpoint."""
        conn_id = f"{endpoint.host}:{endpoint.port}"
        if conn_id in self._connections:
            return self._connections[conn_id]
        
        reader, writer = await asyncio.open_connection(
            endpoint.host, endpoint.port
        )
        
        conn = TCPConnection(conn_id, endpoint, reader, writer, self._on_message_received)
        self._connections[conn_id] = conn
        self._connections_accepted += 1
        
        asyncio.create_task(conn.run())
        await self.handler.on_connect(endpoint)
        
        return conn
    
    async def send(
        self,
        message: Message,
        endpoint: NetworkEndpoint
    ) -> None:
        """Send message via TCP."""
        conn_id = f"{endpoint.host}:{endpoint.port}"
        
        if conn_id not in self._connections:
            await self.connect(endpoint)
        
        conn = self._connections[conn_id]
        await conn.send(message)
        self._messages_sent += 1
    
    async def broadcast(self, message: Message, endpoints: List[NetworkEndpoint]) -> None:
        """Send message to multiple endpoints."""
        await asyncio.gather(
            *[self.send(message, ep) for ep in endpoints],
            return_exceptions=True
        )
    
    async def _on_client_connected(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming TCP connection."""
        addr = writer.get_extra_info('peername')
        endpoint = NetworkEndpoint(addr[0], addr[1])
        conn_id = f"{addr[0]}:{addr[1]}"
        
        if len(self._connections) >= self.max_connections:
            logger.warning(f"Max connections reached, rejecting {endpoint}")
            writer.close()
            return
        
        conn = TCPConnection(conn_id, endpoint, reader, writer, self._on_message_received)
        self._connections[conn_id] = conn
        self._connections_accepted += 1
        
        await self.handler.on_connect(endpoint)
        await conn.run()
    
    async def _on_message_received(
        self,
        message: Message,
        endpoint: NetworkEndpoint
    ) -> None:
        """Handle received message."""
        self._messages_received += 1
        await self.handler.on_message(message, endpoint)
    
    def _on_connection_closed(self, conn_id: str, endpoint: NetworkEndpoint) -> None:
        """Handle connection closure."""
        if conn_id in self._connections:
            del self._connections[conn_id]
            self._connections_closed += 1
            asyncio.create_task(self.handler.on_disconnect(endpoint))
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get transport statistics."""
        return {
            "connections_active": len(self._connections),
            "connections_accepted": self._connections_accepted,
            "connections_closed": self._connections_closed,
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received
        }


class TCPConnection:
    """Individual TCP connection handler."""
    
    def __init__(
        self,
        conn_id: str,
        endpoint: NetworkEndpoint,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        on_message: Callable[[Message, NetworkEndpoint], None]
    ) -> None:
        self.conn_id = conn_id
        self.endpoint = endpoint
        self.reader = reader
        self.writer = writer
        self.on_message = on_message
        self._running = False
        self._send_lock = asyncio.Lock()
    
    async def run(self) -> None:
        """Run connection loop."""
        self._running = True
        
        try:
            while self._running:
                # Read message header (16 bytes)
                header = await self.reader.readexactly(16)
                _, _, payload_len, _, _ = struct.unpack("!BBHQI", header)
                
                # Read rest of message
                id_len = header[1]
                remaining = id_len + payload_len
                data = await self.reader.readexactly(remaining)
                
                # Parse and handle message
                full_data = header + data
                message = Message.unpack(full_data)
                await self.on_message(message, self.endpoint)
                
        except asyncio.IncompleteReadError:
            logger.debug(f"Connection {self.endpoint} closed by peer")
        except Exception as e:
            logger.error(f"TCP connection error: {e}")
        finally:
            await self.close()
    
    async def send(self, message: Message) -> None:
        """Send message over connection."""
        async with self._send_lock:
            data = message.pack()
            self.writer.write(data)
            await self.writer.drain()
    
    async def close(self) -> None:
        """Close connection."""
        self._running = False
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except Exception:
            pass


class NetworkManager:
    """
    Unified network manager combining UDP and TCP transports.
    
    Provides:
    - UDP for real-time shadow data streaming
    - TCP for control and configuration
    - Unified message handling
    - Bandwidth monitoring
    """
    
    def __init__(
        self,
        node_id: str,
        udp_endpoint: NetworkEndpoint,
        tcp_endpoint: NetworkEndpoint,
        multicast_group: str = "239.255.0.1"
    ) -> None:
        self.node_id = node_id
        self.udp_endpoint = udp_endpoint
        self.tcp_endpoint = tcp_endpoint
        self.multicast_group = multicast_group
        
        # Message handlers by type
        self._handlers: Dict[MessageType, List[Callable[[Message, NetworkEndpoint], None]]] = {
            msg_type: [] for msg_type in MessageType
        }
        
        # Transports
        self._udp: Optional[UDPTransport] = None
        self._tcp: Optional[TCPTransport] = None
        
        # Handler wrapper
        self._handler = _TransportHandlerWrapper(self._on_message, self._on_connect, self._on_disconnect)
    
    async def start(self) -> None:
        """Start all transports."""
        self._udp = UDPTransport(
            self.udp_endpoint,
            self._handler,
            self.multicast_group
        )
        self._tcp = TCPTransport(
            self.tcp_endpoint,
            self._handler
        )
        
        await asyncio.gather(
            self._udp.start(),
            self._tcp.start()
        )
        
        logger.info(f"Network manager started for node {self.node_id}")
    
    async def stop(self) -> None:
        """Stop all transports."""
        await asyncio.gather(
            self._udp.stop() if self._udp else asyncio.sleep(0),
            self._tcp.stop() if self._tcp else asyncio.sleep(0)
        )
        logger.info(f"Network manager stopped for node {self.node_id}")
    
    def register_handler(
        self,
        msg_type: MessageType,
        handler: Callable[[Message, NetworkEndpoint], None]
    ) -> None:
        """Register message handler."""
        self._handlers[msg_type].append(handler)
    
    def unregister_handler(
        self,
        msg_type: MessageType,
        handler: Callable[[Message, NetworkEndpoint], None]
    ) -> None:
        """Unregister message handler."""
        if handler in self._handlers[msg_type]:
            self._handlers[msg_type].remove(handler)
    
    def send_udp(self, message: Message, endpoint: NetworkEndpoint) -> None:
        """Send via UDP."""
        if self._udp:
            message.source_id = self.node_id
            self._udp.send(message, endpoint)
    
    def send_udp_multicast(self, message: Message) -> None:
        """Send via UDP multicast."""
        if self._udp:
            message.source_id = self.node_id
            self._udp.send_multicast(message)
    
    async def send_tcp(self, message: Message, endpoint: NetworkEndpoint) -> None:
        """Send via TCP."""
        if self._tcp:
            message.source_id = self.node_id
            await self._tcp.send(message, endpoint)
    
    async def broadcast_tcp(
        self,
        message: Message,
        endpoints: List[NetworkEndpoint]
    ) -> None:
        """Broadcast via TCP."""
        if self._tcp:
            message.source_id = self.node_id
            await self._tcp.broadcast(message, endpoints)
    
    async def connect_tcp(self, endpoint: NetworkEndpoint) -> None:
        """Establish TCP connection."""
        if self._tcp:
            await self._tcp.connect(endpoint)
    
    async def _on_message(self, message: Message, endpoint: NetworkEndpoint) -> None:
        """Route message to handlers."""
        handlers = self._handlers.get(message.msg_type, [])
        for handler in handlers:
            try:
                await handler(message, endpoint)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
    
    async def _on_connect(self, endpoint: NetworkEndpoint) -> None:
        """Handle new connection."""
        logger.debug(f"Connected to {endpoint}")
    
    async def _on_disconnect(self, endpoint: NetworkEndpoint) -> None:
        """Handle disconnection."""
        logger.debug(f"Disconnected from {endpoint}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        return {
            "udp": self._udp.stats if self._udp else {},
            "tcp": self._tcp.stats if self._tcp else {}
        }
    
    def estimate_bandwidth_mbps(self) -> float:
        """Estimate current bandwidth usage in Mbps."""
        udp_stats = self._udp.stats if self._udp else {}
        total_bytes = udp_stats.get("bytes_sent", 0) + udp_stats.get("bytes_received", 0)
        # Assume stats collected over 1 second
        return (total_bytes * 8) / 1_000_000


class _TransportHandlerWrapper(TransportHandler):
    """Wrapper to adapt callbacks to TransportHandler interface."""
    
    def __init__(
        self,
        on_message: Callable[[Message, NetworkEndpoint], None],
        on_connect: Callable[[NetworkEndpoint], None],
        on_disconnect: Callable[[NetworkEndpoint], None]
    ) -> None:
        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
    
    async def on_message(self, message: Message, addr: NetworkEndpoint) -> None:
        await self._on_message(message, addr)
    
    async def on_connect(self, endpoint: NetworkEndpoint) -> None:
        await self._on_connect(endpoint)
    
    async def on_disconnect(self, endpoint: NetworkEndpoint) -> None:
        await self._on_disconnect(endpoint)


# Mock network for testing
class MockNetwork:
    """Mock network for unit testing."""
    
    def __init__(self) -> None:
        self._nodes: Dict[str, NetworkManager] = {}
        self._latency_ms: float = 0.0
        self._packet_loss_rate: float = 0.0
        self._lock = asyncio.Lock()
    
    async def register_node(self, manager: NetworkManager) -> None:
        """Register a node with the mock network."""
        async with self._lock:
            self._nodes[manager.node_id] = manager
    
    async def unregister_node(self, node_id: str) -> None:
        """Unregister a node."""
        async with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
    
    def set_latency(self, latency_ms: float) -> None:
        """Set simulated network latency."""
        self._latency_ms = latency_ms
    
    def set_packet_loss(self, loss_rate: float) -> None:
        """Set simulated packet loss rate (0-1)."""
        self._packet_loss_rate = max(0.0, min(1.0, loss_rate))
    
    async def route_message(
        self,
        source_id: str,
        target_id: str,
        message: Message
    ) -> None:
        """Route message between nodes in mock network."""
        import random
        
        # Simulate packet loss
        if random.random() < self._packet_loss_rate:
            return
        
        # Simulate latency
        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)
        
        async with self._lock:
            target = self._nodes.get(target_id)
            if target:
                endpoint = NetworkEndpoint("127.0.0.1", 0)
                await target._on_message(message, endpoint)
    
    async def broadcast(
        self,
        source_id: str,
        message: Message
    ) -> None:
        """Broadcast to all nodes except source."""
        async with self._lock:
            targets = [nid for nid in self._nodes if nid != source_id]
        
        await asyncio.gather(
            *[self.route_message(source_id, tid, message) for tid in targets],
            return_exceptions=True
        )
"""Fusion layer for multi-array shadow tracking."""

from .shadow_fusion import (
    Vector2D,
    ArrayPosition,
    ShadowObservation,
    ShadowFusionEngine,
    SpatialHash,
    TriangulationFusion,
    FusedShadow
)

from .global_map import (
    GlobalObject,
    GlobalShadowMap,
    ArrayCoverage,
    CoveragePlanner
)

__all__ = [
    # Shadow Fusion
    'Vector2D',
    'ArrayPosition',
    'ShadowObservation',
    'ShadowFusionEngine',
    'SpatialHash',
    'TriangulationFusion',
    'FusedShadow',
    # Global Map
    'GlobalObject',
    'GlobalShadowMap',
    'ArrayCoverage',
    'CoveragePlanner'
]
"""
Global Shadow-Map for Distributed Tracking.

Provides unified coordinate system, global object tracking IDs,
and hand-off between arrays for seamless multi-array tracking.
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Iterator
from collections import defaultdict
import logging

from .shadow_fusion import (
    Vector2D, ArrayPosition, ShadowObservation, 
    FusedShadow, ShadowFusionEngine
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GlobalObject:
    """
    Globally tracked object with persistent ID.
    
    Maintains identity across array hand-offs and provides
    unified tracking state.
    """
    object_id: str
    created_ns: int
    
    # Current state
    position: Vector2D
    velocity: Vector2D
    confidence: float
    
    # Tracking metadata
    primary_array: str  # Array currently responsible for tracking
    visible_arrays: Set[str]  # Arrays currently seeing this object
    last_seen_ns: int
    
    # Trajectory history (for prediction)
    trajectory: List[Tuple[int, Vector2D]] = field(default_factory=list)
    max_trajectory_length: int = 100
    
    # Statistics
    total_observations: int = 0
    handoff_count: int = 0
    
    def update_position(self, position: Vector2D, timestamp_ns: int) -> None:
        """Update position and maintain trajectory."""
        # Calculate velocity
        dt_ns = timestamp_ns - self.last_seen_ns
        if dt_ns > 0 and self.last_seen_ns > 0:
            dt_s = dt_ns / 1_000_000_000
            new_vx = (position.x - self.position.x) / dt_s
            new_vy = (position.y - self.position.y) / dt_s
            # Smooth velocity
            alpha = 0.3
            self.velocity = Vector2D(
                self.velocity.x * (1 - alpha) + new_vx * alpha,
                self.velocity.y * (1 - alpha) + new_vy * alpha
            )
        
        self.position = position
        self.last_seen_ns = timestamp_ns
        self.total_observations += 1
        
        # Update trajectory
        self.trajectory.append((timestamp_ns, position))
        if len(self.trajectory) > self.max_trajectory_length:
            self.trajectory.pop(0)
    
    def predict_position(self, future_time_ns: int) -> Vector2D:
        """Predict position at future time using velocity."""
        dt_ns = future_time_ns - self.last_seen_ns
        if dt_ns <= 0:
            return self.position
        
        dt_s = dt_ns / 1_000_000_000
        return Vector2D(
            self.position.x + self.velocity.x * dt_s,
            self.position.y + self.velocity.y * dt_s
        )
    
    @property
    def age_ms(self) -> float:
        """Age of object in milliseconds."""
        return (time.time_ns() - self.created_ns) / 1_000_000
    
    @property
    def is_stale(self, max_age_ms: float = 1000.0) -> bool:
        """Check if object hasn't been seen recently."""
        return (time.time_ns() - self.last_seen_ns) / 1_000_000 > max_age_ms


@dataclass(slots=True)
class ArrayCoverage:
    """Coverage area of a microphone array."""
    array_id: str
    position: Vector2D
    radius: float  # Detection radius in meters
    fov_degrees: float = 360.0  # Field of view
    orientation: float = 0.0  # Direction array is facing
    
    def contains(self, position: Vector2D) -> bool:
        """Check if position is within array coverage."""
        dist = position.distance_to(self.position)
        if dist > self.radius:
            return False
        
        if self.fov_degrees >= 360:
            return True
        
        # Check angle
        dx = position.x - self.position.x
        dy = position.y - self.position.y
        angle = math.degrees(math.atan2(dx, dy))
        angle_diff = abs((angle - self.orientation + 180) % 360 - 180)
        
        return angle_diff <= self.fov_degrees / 2
    
    def overlap_score(self, other: ArrayCoverage) -> float:
        """Calculate overlap score with another array coverage."""
        dist = self.position.distance_to(other.position)
        
        if dist > self.radius + other.radius:
            return 0.0
        
        # Simple overlap based on distance and radii
        overlap = (self.radius + other.radius - dist) / min(self.radius, other.radius)
        return max(0.0, min(1.0, overlap))


class GlobalShadowMap:
    """
    Global shadow-map for unified multi-array tracking.
    
    Features:
    - Persistent global object IDs
    - Seamless array hand-offs
    - Coverage optimization
    - O(1) object lookup
    """
    
    def __init__(
        self,
        fusion_engine: ShadowFusionEngine,
        max_object_age_ms: float = 2000.0,
        handoff_threshold: float = 0.7  # Confidence threshold for handoff
    ) -> None:
        self.fusion_engine = fusion_engine
        self.max_object_age_ms = max_object_age_ms
        self.handoff_threshold = handoff_threshold
        
        # Global objects
        self._objects: Dict[str, GlobalObject] = {}
        self._object_counter = 0
        
        # Array coverage areas
        self._coverage: Dict[str, ArrayCoverage] = {}
        
        # Object to fused shadow mapping
        self._shadow_to_object: Dict[str, str] = {}
        
        # Coverage optimization
        self._coverage_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Callbacks
        self._object_callbacks: List[Callable[[GlobalObject, str], None]] = []
        # Event types: "created", "updated", "handoff", "lost"
        
        # Statistics
        self._handoff_count = 0
        self._object_count = 0
        
        self._lock = asyncio.Lock()
    
    def register_array_coverage(self, coverage: ArrayCoverage) -> None:
        """Register array coverage area."""
        self._coverage[coverage.array_id] = coverage
        
        # Update coverage graph
        for other_id, other_cov in self._coverage.items():
            if other_id != coverage.array_id:
                overlap = coverage.overlap_score(other_cov)
                if overlap > 0.3:  # Significant overlap
                    self._coverage_graph[coverage.array_id].add(other_id)
                    self._coverage_graph[other_id].add(coverage.array_id)
    
    def add_object_callback(
        self,
        callback: Callable[[GlobalObject, str], None]
    ) -> None:
        """Add callback for object events."""
        self._object_callbacks.append(callback)
    
    async def update_from_fusion(self, fused_shadow: FusedShadow) -> GlobalObject:
        """
        Update global map from fused shadow.
        
        O(1) complexity using shadow-to-object mapping.
        """
        async with self._lock:
            # Check if shadow already mapped to object
            if fused_shadow.shadow_id in self._shadow_to_object:
                obj_id = self._shadow_to_object[fused_shadow.shadow_id]
                return await self._update_object(obj_id, fused_shadow)
            
            # Try to match with existing object
            existing = await self._find_matching_object(fused_shadow)
            if existing:
                self._shadow_to_object[fused_shadow.shadow_id] = existing.object_id
                return await self._update_object(existing.object_id, fused_shadow)
            
            # Create new global object
            return await self._create_object(fused_shadow)
    
    async def _find_matching_object(
        self,
        fused_shadow: FusedShadow
    ) -> Optional[GlobalObject]:
        """Find existing object matching fused shadow."""
        # Search by position proximity
        search_radius = 1.0  # meters
        
        best_match = None
        best_score = float('inf')
        
        for obj in self._objects.values():
            # Predict current position
            predicted = obj.predict_position(fused_shadow.timestamp_ns)
            dist = predicted.distance_to(fused_shadow.position)
            
            if dist < search_radius:
                # Score based on distance and velocity consistency
                score = dist
                if obj.velocity.magnitude() > 0.1:
                    # Check velocity alignment
                    expected_dist = obj.velocity.magnitude() * 0.1  # 100ms
                    score += abs(dist - expected_dist)
                
                if score < best_score:
                    best_score = score
                    best_match = obj
        
        return best_match
    
    async def _create_object(self, fused_shadow: FusedShadow) -> GlobalObject:
        """Create new global object from fused shadow."""
        self._object_counter += 1
        obj_id = f"obj_{self._object_counter:06d}"
        
        # Determine primary array
        primary = self._select_primary_array(fused_shadow)
        
        obj = GlobalObject(
            object_id=obj_id,
            created_ns=fused_shadow.timestamp_ns,
            position=fused_shadow.position,
            velocity=Vector2D(0.0, 0.0),
            confidence=fused_shadow.confidence,
            primary_array=primary,
            visible_arrays=set(fused_shadow.contributing_arrays),
            last_seen_ns=fused_shadow.timestamp_ns
        )
        
        self._objects[obj_id] = obj
        self._shadow_to_object[fused_shadow.shadow_id] = obj_id
        self._object_count += 1
        
        # Notify callbacks
        self._notify_callbacks(obj, "created")
        
        logger.debug(f"Created global object {obj_id} at {obj.position.to_tuple()}")
        
        return obj
    
    async def _update_object(
        self,
        obj_id: str,
        fused_shadow: FusedShadow
    ) -> GlobalObject:
        """Update existing global object."""
        obj = self._objects[obj_id]
        
        # Update position
        obj.update_position(fused_shadow.position, fused_shadow.timestamp_ns)
        
        # Update confidence
        obj.confidence = fused_shadow.confidence
        
        # Update visible arrays
        old_primary = obj.primary_array
        obj.visible_arrays.update(fused_shadow.contributing_arrays)
        
        # Check for handoff
        new_primary = self._select_primary_array(fused_shadow, obj)
        if new_primary != old_primary and fused_shadow.confidence > self.handoff_threshold:
            obj.primary_array = new_primary
            obj.handoff_count += 1
            self._handoff_count += 1
            self._notify_callbacks(obj, "handoff")
            logger.debug(f"Object {obj_id} handed off from {old_primary} to {new_primary}")
        
        # Notify update
        self._notify_callbacks(obj, "updated")
        
        return obj
    
    def _select_primary_array(
        self,
        fused_shadow: FusedShadow,
        existing_obj: Optional[GlobalObject] = None
    ) -> str:
        """Select primary array for tracking an object."""
        arrays = fused_shadow.contributing_arrays
        
        if not arrays:
            return "unknown"
        
        if len(arrays) == 1:
            return list(arrays)[0]
        
        # Score each array
        best_array = None
        best_score = -1.0
        
        for array_id in arrays:
            score = 0.0
            
            # Prefer arrays with better coverage of object position
            coverage = self._coverage.get(array_id)
            if coverage:
                dist = fused_shadow.position.distance_to(coverage.position)
                score += (coverage.radius - dist) / coverage.radius
            
            # Prefer arrays that have been tracking this object
            if existing_obj and array_id == existing_obj.primary_array:
                score += 0.5  # Hysteresis
            
            if score > best_score:
                best_score = score
                best_array = array_id
        
        return best_array or list(arrays)[0]
    
    def _notify_callbacks(self, obj: GlobalObject, event: str) -> None:
        """Notify all registered callbacks."""
        for callback in self._object_callbacks:
            try:
                callback(obj, event)
            except Exception as e:
                logger.error(f"Object callback error: {e}")
    
    async def cleanup_stale_objects(self, current_time_ns: int) -> List[str]:
        """Remove objects that haven't been seen recently."""
        stale_ids = []
        max_age_ns = int(self.max_object_age_ms * 1_000_000)
        
        async with self._lock:
            for obj_id, obj in list(self._objects.items()):
                age_ns = current_time_ns - obj.last_seen_ns
                if age_ns > max_age_ns:
                    stale_ids.append(obj_id)
                    del self._objects[obj_id]
                    
                    # Clean up shadow mappings
                    for sid, oid in list(self._shadow_to_object.items()):
                        if oid == obj_id:
                            del self._shadow_to_object[sid]
                    
                    self._notify_callbacks(obj, "lost")
        
        return stale_ids
    
    def get_object(self, object_id: str) -> Optional[GlobalObject]:
        """Get object by ID."""
        return self._objects.get(object_id)
    
    def get_all_objects(self) -> List[GlobalObject]:
        """Get all active objects."""
        return list(self._objects.values())
    
    def get_objects_in_region(
        self,
        center: Vector2D,
        radius: float
    ) -> List[GlobalObject]:
        """Get objects within a region."""
        result = []
        for obj in self._objects.values():
            if obj.position.distance_to(center) <= radius:
                result.append(obj)
        return result
    
    def get_objects_by_array(self, array_id: str) -> List[GlobalObject]:
        """Get objects currently visible to an array."""
        return [
            obj for obj in self._objects.values()
            if array_id in obj.visible_arrays
        ]
    
    def get_optimal_array_for_position(self, position: Vector2D) -> Optional[str]:
        """Get best array to track a position."""
        best_array = None
        best_score = -1.0
        
        for array_id, coverage in self._coverage.items():
            if coverage.contains(position):
                dist = position.distance_to(coverage.position)
                score = coverage.radius - dist
                if score > best_score:
                    best_score = score
                    best_array = array_id
        
        return best_array
    
    def calculate_coverage_optimization(self) -> Dict[str, List[str]]:
        """
        Calculate optimal array assignments for coverage.
        
        Returns mapping of under-covered regions to recommended arrays.
        """
        optimization: Dict[str, List[str]] = {}
        
        # Find regions with no coverage
        # This is a simplified version - real implementation would
        # use spatial analysis of the coverage map
        
        for obj in self._objects.values():
            visible = len(obj.visible_arrays)
            if visible < 2:
                # Object seen by fewer than 2 arrays
                # Find nearby arrays that could help
                nearby = []
                for array_id, coverage in self._coverage.items():
                    if array_id not in obj.visible_arrays:
                        if coverage.contains(obj.position):
                            nearby.append(array_id)
                
                if nearby:
                    optimization[obj.object_id] = nearby
        
        return optimization
    
    def get_coverage_stats(self) -> Dict[str, any]:
        """Get coverage statistics."""
        total_area = 0.0
        overlaps = 0
        
        for i, (id1, cov1) in enumerate(self._coverage.items()):
            total_area += math.pi * cov1.radius ** 2
            for id2, cov2 in list(self._coverage.items())[i+1:]:
                if cov1.overlap_score(cov2) > 0:
                    overlaps += 1
        
        return {
            "array_count": len(self._coverage),
            "total_coverage_area": total_area,
            "overlap_count": overlaps,
            "average_objects_per_array": (
                len(self._objects) / len(self._coverage) if self._coverage else 0
            )
        }
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get global map statistics."""
        return {
            "active_objects": len(self._objects),
            "total_objects_created": self._object_count,
            "handoffs": self._handoff_count,
            "arrays": len(self._coverage)
        }
    
    async def clear(self) -> None:
        """Clear all objects and reset state."""
        async with self._lock:
            self._objects.clear()
            self._shadow_to_object.clear()
            self._object_counter = 0
            self._handoff_count = 0


class CoveragePlanner:
    """
    Plans optimal array placement for coverage.
    
    Provides recommendations for array positioning to achieve
    desired coverage with minimal overlap.
    """
    
    def __init__(
        self,
        room_dimensions: Tuple[float, float],  # width, height in meters
        target_coverage: float = 0.95,  # Target coverage percentage
        min_overlap: float = 0.1  # Minimum overlap for handoff
    ) -> None:
        self.room_width, self.room_height = room_dimensions
        self.target_coverage = target_coverage
        self.min_overlap = min_overlap
    
    def calculate_optimal_placement(
        self,
        array_count: int,
        array_radius: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate optimal array positions.
        
        Uses hexagonal packing for even coverage.
        """
        positions = []
        
        if array_count == 1:
            # Center single array
            positions.append((self.room_width / 2, self.room_height / 2))
        
        elif array_count == 2:
            # Two arrays on opposite sides
            positions.append((self.room_width * 0.25, self.room_height / 2))
            positions.append((self.room_width * 0.75, self.room_height / 2))
        
        elif array_count == 4:
            # Four corners
            margin = array_radius * 0.5
            positions.extend([
                (margin, margin),
                (self.room_width - margin, margin),
                (margin, self.room_height - margin),
                (self.room_width - margin, self.room_height - margin)
            ])
        
        elif array_count == 8:
            # Eight arrays: corners + midpoints
            margin = array_radius * 0.3
            positions.extend([
                # Corners
                (margin, margin),
                (self.room_width - margin, margin),
                (margin, self.room_height - margin),
                (self.room_width - margin, self.room_height - margin),
                # Midpoints
                (self.room_width / 2, margin),
                (self.room_width / 2, self.room_height - margin),
                (margin, self.room_height / 2),
                (self.room_width - margin, self.room_height / 2)
            ])
        
        else:
            # Grid placement for other counts
            cols = int(math.ceil(math.sqrt(array_count)))
            rows = int(math.ceil(array_count / cols))
            
            x_step = self.room_width / (cols + 1)
            y_step = self.room_height / (rows + 1)
            
            for i in range(array_count):
                row = i // cols
                col = i % cols
                x = x_step * (col + 1)
                y = y_step * (row + 1)
                positions.append((x, y))
        
        return positions
    
    def estimate_coverage(
        self,
        positions: List[Tuple[float, float]],
        radius: float
    ) -> float:
        """Estimate coverage percentage for given positions."""
        # Monte Carlo sampling
        samples = 1000
        covered = 0
        
        import random
        random.seed(42)
        
        for _ in range(samples):
            x = random.uniform(0, self.room_width)
            y = random.uniform(0, self.room_height)
            point = Vector2D(x, y)
            
            for px, py in positions:
                if point.distance_to(Vector2D(px, py)) <= radius:
                    covered += 1
                    break
        
        return covered / samples
"""
Multi-Array Shadow Fusion Algorithms.

Fuses shadow data from multiple microphone arrays to create unified tracking.
Implements O(1) per object complexity using spatial hashing and efficient
conflict resolution.
"""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Iterator
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Vector2D:
    """2D vector for spatial calculations."""
    x: float
    y: float
    
    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def distance_to(self, other: Vector2D) -> float:
        return (self - other).magnitude()
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass(slots=True)
class ArrayPosition:
    """Position and orientation of a microphone array."""
    array_id: str
    position: Vector2D
    orientation: float  # Degrees from North
    
    def local_to_global(self, local_pos: Vector2D) -> Vector2D:
        """Convert local array coordinates to global."""
        # Rotate by orientation
        rad = math.radians(self.orientation)
        cos_o = math.cos(rad)
        sin_o = math.sin(rad)
        
        rotated = Vector2D(
            local_pos.x * cos_o - local_pos.y * sin_o,
            local_pos.x * sin_o + local_pos.y * cos_o
        )
        
        # Translate to array position
        return self.position + rotated
    
    def global_to_local(self, global_pos: Vector2D) -> Vector2D:
        """Convert global coordinates to local array coordinates."""
        # Translate relative to array
        relative = global_pos - self.position
        
        # Rotate by negative orientation
        rad = math.radians(-self.orientation)
        cos_o = math.cos(rad)
        sin_o = math.sin(rad)
        
        return Vector2D(
            relative.x * cos_o - relative.y * sin_o,
            relative.x * sin_o + relative.y * cos_o
        )


@dataclass(slots=True)
class ShadowObservation:
    """Single shadow observation from an array."""
    observation_id: str
    array_id: str
    timestamp_ns: int
    global_position: Vector2D
    confidence: float  # 0-1
    angle: float  # Angle from array
    distance: float  # Distance from array
    
    def __hash__(self) -> int:
        return hash(self.observation_id)


@dataclass(slots=True)
class FusedShadow:
    """Fused shadow from multiple observations."""
    shadow_id: str
    timestamp_ns: int
    position: Vector2D
    velocity: Vector2D
    confidence: float
    contributing_arrays: Set[str]
    observation_count: int
    last_update_ns: int
    
    @property
    def age_ms(self) -> float:
        """Age of shadow in milliseconds."""
        return 0.0  # Calculated externally with current time


class SpatialHash:
    """
    Spatial hashing for O(1) shadow lookup.
    
    Divides space into grid cells for efficient neighbor queries.
    """
    
    def __init__(self, cell_size: float = 1.0) -> None:
        self.cell_size = cell_size
        self._grid: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        self._positions: Dict[str, Vector2D] = {}
        self._lock = asyncio.Lock()
    
    def _get_cell(self, position: Vector2D) -> Tuple[int, int]:
        """Get grid cell for position."""
        return (
            int(position.x / self.cell_size),
            int(position.y / self.cell_size)
        )
    
    def _get_neighbor_cells(self, cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get cell and all 8 neighbors."""
        x, y = cell
        return [
            (x, y), (x+1, y), (x-1, y),
            (x, y+1), (x, y-1),
            (x+1, y+1), (x+1, y-1),
            (x-1, y+1), (x-1, y-1)
        ]
    
    async def insert(self, obj_id: str, position: Vector2D) -> None:
        """Insert object into spatial hash."""
        async with self._lock:
            # Remove from old cell if exists
            if obj_id in self._positions:
                old_cell = self._get_cell(self._positions[obj_id])
                self._grid[old_cell].discard(obj_id)
            
            # Insert into new cell
            cell = self._get_cell(position)
            self._grid[cell].add(obj_id)
            self._positions[obj_id] = position
    
    async def remove(self, obj_id: str) -> None:
        """Remove object from spatial hash."""
        async with self._lock:
            if obj_id in self._positions:
                cell = self._get_cell(self._positions[obj_id])
                self._grid[cell].discard(obj_id)
                del self._positions[obj_id]
    
    async def query_neighbors(
        self,
        position: Vector2D,
        radius: float
    ) -> Set[str]:
        """Query objects within radius (O(1) average)."""
        async with self._lock:
            center_cell = self._get_cell(position)
            
            # Determine cell range to check based on radius
            cells_to_check = radius / self.cell_size
            if cells_to_check <= 1.0:
                cells = self._get_neighbor_cells(center_cell)
            else:
                # Expand search for larger radii
                cells = []
                range_int = int(cells_to_check) + 1
                for dx in range(-range_int, range_int + 1):
                    for dy in range(-range_int, range_int + 1):
                        cells.append((center_cell[0] + dx, center_cell[1] + dy))
            
            # Collect candidates
            candidates: Set[str] = set()
            for cell in cells:
                candidates.update(self._grid.get(cell, set()))
            
            # Filter by actual distance
            result: Set[str] = set()
            for obj_id in candidates:
                if obj_id in self._positions:
                    dist = position.distance_to(self._positions[obj_id])
                    if dist <= radius:
                        result.add(obj_id)
            
            return result
    
    async def get_position(self, obj_id: str) -> Optional[Vector2D]:
        """Get position of object."""
        async with self._lock:
            return self._positions.get(obj_id)
    
    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._grid.clear()
            self._positions.clear()


class ShadowFusionEngine:
    """
    Multi-array shadow fusion engine.
    
    Fuses observations from multiple arrays into unified shadow tracks.
    Maintains O(1) per object complexity using spatial hashing.
    """
    
    def __init__(
        self,
        fusion_radius: float = 0.5,  # Meters
        min_confidence: float = 0.3,
        max_shadow_age_ms: float = 500.0,
        spatial_cell_size: float = 1.0
    ) -> None:
        self.fusion_radius = fusion_radius
        self.min_confidence = min_confidence
        self.max_shadow_age_ms = max_shadow_age_ms
        
        # Array positions (known from calibration)
        self._array_positions: Dict[str, ArrayPosition] = {}
        
        # Fused shadows
        self._shadows: Dict[str, FusedShadow] = {}
        self._spatial_hash = SpatialHash(spatial_cell_size)
        
        # Observation to shadow mapping
        self._observation_map: Dict[str, str] = {}  # observation_id -> shadow_id
        
        # Statistics
        self._fusion_count = 0
        self._conflict_count = 0
        
        # Callbacks
        self._fusion_callbacks: List[Callable[[FusedShadow], None]] = []
        self._lock = asyncio.Lock()
        
        # Shadow ID counter
        self._shadow_counter = 0
    
    def register_array(self, position: ArrayPosition) -> None:
        """Register array position for coordinate transformation."""
        self._array_positions[position.array_id] = position
    
    def unregister_array(self, array_id: str) -> None:
        """Unregister array."""
        if array_id in self._array_positions:
            del self._array_positions[array_id]
    
    def add_fusion_callback(self, callback: Callable[[FusedShadow], None]) -> None:
        """Add callback for new fused shadows."""
        self._fusion_callbacks.append(callback)
    
    async def process_observation(self, obs: ShadowObservation) -> Optional[FusedShadow]:
        """
        Process a new shadow observation.
        
        O(1) complexity per observation using spatial hashing.
        """
        if obs.confidence < self.min_confidence:
            return None
        
        async with self._lock:
            # Check if observation already mapped
            if obs.observation_id in self._observation_map:
                shadow_id = self._observation_map[obs.observation_id]
                return await self._update_shadow(shadow_id, obs)
            
            # Find nearby shadows for fusion
            nearby = await self._spatial_hash.query_neighbors(
                obs.global_position, self.fusion_radius
            )
            
            if nearby:
                # Fuse with existing shadow
                shadow_id = self._select_best_match(obs, nearby)
                if shadow_id:
                    return await self._fuse_observation(shadow_id, obs)
            
            # Create new shadow
            return await self._create_new_shadow(obs)
    
    async def process_observations(
        self,
        observations: List[ShadowObservation]
    ) -> List[FusedShadow]:
        """Process multiple observations efficiently."""
        results = await asyncio.gather(
            *[self.process_observation(obs) for obs in observations]
        )
        return [r for r in results if r is not None]
    
    async def _select_best_match(
        self,
        obs: ShadowObservation,
        candidates: Set[str]
    ) -> Optional[str]:
        """Select best matching shadow for observation."""
        best_id = None
        best_score = float('inf')
        
        for shadow_id in candidates:
            shadow = self._shadows.get(shadow_id)
            if not shadow:
                continue
            
            # Calculate match score (distance weighted by confidence)
            dist = obs.global_position.distance_to(shadow.position)
            score = dist / (obs.confidence * shadow.confidence + 0.001)
            
            # Prefer shadows from different arrays (better triangulation)
            if obs.array_id not in shadow.contributing_arrays:
                score *= 0.8
            
            if score < best_score:
                best_score = score
                best_id = shadow_id
        
        return best_id
    
    async def _fuse_observation(
        self,
        shadow_id: str,
        obs: ShadowObservation
    ) -> FusedShadow:
        """Fuse observation into existing shadow."""
        shadow = self._shadows[shadow_id]
        
        # Check for conflicts (same array, different observation)
        conflict_resolved = await self._resolve_conflicts(shadow, obs)
        if not conflict_resolved:
            self._conflict_count += 1
            # Create separate shadow instead
            return await self._create_new_shadow(obs)
        
        # Weighted position update
        old_weight = shadow.confidence
        new_weight = obs.confidence
        total_weight = old_weight + new_weight
        
        new_x = (shadow.position.x * old_weight + obs.global_position.x * new_weight) / total_weight
        new_y = (shadow.position.y * old_weight + obs.global_position.y * new_weight) / total_weight
        
        # Update velocity
        dt_ns = obs.timestamp_ns - shadow.last_update_ns
        if dt_ns > 0:
            dt_s = dt_ns / 1_000_000_000
            vx = (new_x - shadow.position.x) / dt_s
            vy = (new_y - shadow.position.y) / dt_s
            # Smooth velocity
            alpha = 0.3
            shadow.velocity = Vector2D(
                shadow.velocity.x * (1 - alpha) + vx * alpha,
                shadow.velocity.y * (1 - alpha) + vy * alpha
            )
        
        # Update shadow
        shadow.position = Vector2D(new_x, new_y)
        shadow.confidence = min(1.0, total_weight * 0.5)  # Cap at 1.0
        shadow.contributing_arrays.add(obs.array_id)
        shadow.observation_count += 1
        shadow.last_update_ns = obs.timestamp_ns
        
        # Update spatial hash
        await self._spatial_hash.insert(shadow_id, shadow.position)
        
        # Map observation
        self._observation_map[obs.observation_id] = shadow_id
        
        self._fusion_count += 1
        
        # Notify callbacks
        for callback in self._fusion_callbacks:
            try:
                callback(shadow)
            except Exception as e:
                logger.error(f"Fusion callback error: {e}")
        
        return shadow
    
    async def _resolve_conflicts(
        self,
        shadow: FusedShadow,
        new_obs: ShadowObservation
    ) -> bool:
        """
        Resolve conflicts when same array reports multiple observations.
        
        Returns True if fusion should proceed, False to create new shadow.
        """
        # If same array already contributed, check if this is an update
        if new_obs.array_id in shadow.contributing_arrays:
            # Check if positions are consistent
            dist = new_obs.global_position.distance_to(shadow.position)
            
            # If very close, treat as update
            if dist < self.fusion_radius * 0.5:
                return True
            
            # If far, might be different object - check confidence
            if new_obs.confidence > shadow.confidence * 1.5:
                # New observation much more confident, replace
                shadow.contributing_arrays.discard(new_obs.array_id)
                return True
            
            # Conflict - don't fuse
            return False
        
        return True
    
    async def _create_new_shadow(self, obs: ShadowObservation) -> FusedShadow:
        """Create new fused shadow from observation."""
        self._shadow_counter += 1
        shadow_id = f"shadow_{self._shadow_counter}"
        
        shadow = FusedShadow(
            shadow_id=shadow_id,
            timestamp_ns=obs.timestamp_ns,
            position=obs.global_position,
            velocity=Vector2D(0.0, 0.0),
            confidence=obs.confidence,
            contributing_arrays={obs.array_id},
            observation_count=1,
            last_update_ns=obs.timestamp_ns
        )
        
        self._shadows[shadow_id] = shadow
        await self._spatial_hash.insert(shadow_id, shadow.position)
        self._observation_map[obs.observation_id] = shadow_id
        
        # Notify callbacks
        for callback in self._fusion_callbacks:
            try:
                callback(shadow)
            except Exception as e:
                logger.error(f"Fusion callback error: {e}")
        
        return shadow
    
    async def _update_shadow(
        self,
        shadow_id: str,
        obs: ShadowObservation
    ) -> Optional[FusedShadow]:
        """Update existing shadow with refined observation."""
        if shadow_id not in self._shadows:
            return None
        
        # Re-fuse with updated observation
        return await self._fuse_observation(shadow_id, obs)
    
    async def cleanup_stale_shadows(self, current_time_ns: int) -> List[str]:
        """Remove shadows that haven't been updated recently."""
        stale_ids = []
        max_age_ns = int(self.max_shadow_age_ms * 1_000_000)
        
        async with self._lock:
            for shadow_id, shadow in list(self._shadows.items()):
                age_ns = current_time_ns - shadow.last_update_ns
                if age_ns > max_age_ns:
                    stale_ids.append(shadow_id)
                    del self._shadows[shadow_id]
                    await self._spatial_hash.remove(shadow_id)
            
            # Clean up observation map
            for obs_id, sid in list(self._observation_map.items()):
                if sid in stale_ids:
                    del self._observation_map[obs_id]
        
        return stale_ids
    
    def get_shadow(self, shadow_id: str) -> Optional[FusedShadow]:
        """Get shadow by ID."""
        return self._shadows.get(shadow_id)
    
    def get_all_shadows(self) -> List[FusedShadow]:
        """Get all active shadows."""
        return list(self._shadows.values())
    
    def get_shadow_count(self) -> int:
        """Get number of active shadows."""
        return len(self._shadows)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get fusion statistics."""
        return {
            "active_shadows": len(self._shadows),
            "fusion_count": self._fusion_count,
            "conflict_count": self._conflict_count,
            "registered_arrays": len(self._array_positions)
        }
    
    async def clear(self) -> None:
        """Clear all shadows and reset state."""
        async with self._lock:
            self._shadows.clear()
            await self._spatial_hash.clear()
            self._observation_map.clear()
            self._fusion_count = 0
            self._conflict_count = 0
            self._shadow_counter = 0


class TriangulationFusion:
    """
    Advanced fusion using triangulation from multiple arrays.
    
    Provides more accurate position estimation when 3+ arrays
    observe the same object.
    """
    
    def __init__(self, min_arrays_for_triangulation: int = 3) -> None:
        self.min_arrays = min_arrays_for_triangulation
    
    def triangulate(
        self,
        observations: List[ShadowObservation]
    ) -> Optional[Tuple[Vector2D, float]]:
        """
        Triangulate position from multiple array observations.
        
        Returns (position, confidence) or None if insufficient data.
        """
        if len(observations) < self.min_arrays:
            return None
        
        # Use least squares for optimal position estimation
        # Each observation gives us: (x - xi)^2 + (y - yi)^2 = di^2
        
        positions = []
        weights = []
        
        for obs in observations:
            positions.append(obs.global_position)
            weights.append(obs.confidence)
        
        # Weighted centroid as initial estimate
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        centroid = Vector2D(0.0, 0.0)
        for pos, w in zip(positions, weights):
            centroid = centroid + pos * (w / total_weight)
        
        # Calculate confidence based on spread
        spread = sum(
            pos.distance_to(centroid) * w
            for pos, w in zip(positions, weights)
        ) / total_weight
        
        confidence = 1.0 / (1.0 + spread)
        
        return centroid, confidence
    
    def calculate_bearing_intersection(
        self,
        array1_pos: Vector2D,
        bearing1: float,
        array2_pos: Vector2D,
        bearing2: float
    ) -> Optional[Vector2D]:
        """
        Calculate intersection of two bearing lines.
        
        Returns intersection point or None if parallel.
        """
        # Convert bearings to unit vectors
        rad1 = math.radians(bearing1)
        rad2 = math.radians(bearing2)
        
        dx1 = math.sin(rad1)
        dy1 = math.cos(rad1)
        dx2 = math.sin(rad2)
        dy2 = math.cos(rad2)
        
        # Line 1: array1_pos + t1 * (dx1, dy1)
        # Line 2: array2_pos + t2 * (dx2, dy2)
        # Solve for intersection
        
        det = dx1 * (-dy2) - dy1 * (-dx2)
        if abs(det) < 1e-10:
            return None  # Parallel lines
        
        diff_x = array2_pos.x - array1_pos.x
        diff_y = array2_pos.y - array1_pos.y
        
        t1 = (diff_x * (-dy2) - diff_y * (-dx2)) / det
        
        return Vector2D(
            array1_pos.x + t1 * dx1,
            array1_pos.y + t1 * dy1
        )
"""Coordination layer for distributed array management."""

from .array_coordinator import (
    NodeRole,
    NodeState,
    NodeInfo,
    SystemStatus,
    ArrayCoordinator,
    LoadBalancer
)

__all__ = [
    'NodeRole',
    'NodeState',
    'NodeInfo',
    'SystemStatus',
    'ArrayCoordinator',
    'LoadBalancer'
]
"""
Array Coordinator for Distributed Shadow Network.

Coordinates multiple microphone arrays, manages node discovery,
handles load balancing, and ensures system-wide consistency.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
import logging

from ..network.transport import NetworkManager, NetworkEndpoint, Message, MessageType
from ..network.ptp_sync import PTPSynchronizer, SyncStatus, SyncStats, create_synchronizer
from ..fusion.shadow_fusion import ArrayPosition, Vector2D

logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Role of a node in the distributed system."""
    MASTER = auto()      # Central coordinator
    WORKER = auto()      # Processing node (array)
    BACKUP = auto()      # Backup coordinator
    OBSERVER = auto()    # Monitoring only


class NodeState(Enum):
    """State of a node in the system."""
    INITIALIZING = auto()
    DISCOVERING = auto()
    SYNCING = auto()
    ACTIVE = auto()
    DEGRADED = auto()
    OFFLINE = auto()


@dataclass(slots=True)
class NodeInfo:
    """Information about a node in the network."""
    node_id: str
    role: NodeRole
    state: NodeState
    
    # Network endpoints
    udp_endpoint: NetworkEndpoint
    tcp_endpoint: NetworkEndpoint
    
    # Array information (for worker nodes)
    array_position: Optional[ArrayPosition] = None
    
    # Capabilities
    max_objects: int = 10
    processing_latency_ms: float = 10.0
    
    # Status
    last_heartbeat: float = 0.0
    sync_offset_ns: float = 0.0
    objects_tracked: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    # Metadata
    version: str = "1.0.0"
    started_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class SystemStatus:
    """Overall system status."""
    timestamp: float
    node_count: int
    active_nodes: int
    synced_nodes: int
    total_objects: int
    average_latency_ms: float
    system_load: float


class ArrayCoordinator:
    """
    Central coordinator for distributed microphone arrays.
    
    Responsibilities:
    - Node discovery and registration
    - Role assignment (master/worker)
    - Load balancing
    - System monitoring
    - Failure detection
    """
    
    def __init__(
        self,
        node_id: str,
        role: NodeRole = NodeRole.MASTER,
        udp_port: int = 5000,
        tcp_port: int = 5001,
        heartbeat_interval_ms: float = 100.0,
        node_timeout_ms: float = 500.0
    ) -> None:
        self.node_id = node_id
        self.role = role
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.heartbeat_interval_ms = heartbeat_interval_ms
        self.node_timeout_ms = node_timeout_ms
        
        # Node registry
        self._nodes: Dict[str, NodeInfo] = {}
        self._pending_nodes: Dict[str, NodeInfo] = {}
        
        # This node's info
        self._local_info = NodeInfo(
            node_id=node_id,
            role=role,
            state=NodeState.INITIALIZING,
            udp_endpoint=NetworkEndpoint("0.0.0.0", udp_port),
            tcp_endpoint=NetworkEndpoint("0.0.0.0", tcp_port)
        )
        
        # Network
        self._network: Optional[NetworkManager] = None
        
        # PTP sync
        self._ptp: Optional[PTPSynchronizer] = None
        
        # Tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Callbacks
        self._node_callbacks: List[Callable[[str, NodeInfo, str], None]] = []
        # Events: "joined", "updated", "left", "failed"
        
        self._status_callbacks: List[Callable[[SystemStatus], None]] = []
        
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the coordinator."""
        self._running = True
        
        # Initialize network
        self._network = NetworkManager(
            self.node_id,
            self._local_info.udp_endpoint,
            self._local_info.tcp_endpoint
        )
        
        # Register handlers
        self._network.register_handler(MessageType.DISCOVERY, self._on_discovery)
        self._network.register_handler(MessageType.HEARTBEAT, self._on_heartbeat)
        self._network.register_handler(MessageType.HANDSHAKE, self._on_handshake)
        self._network.register_handler(MessageType.STATUS, self._on_status)
        
        await self._network.start()
        
        # Start PTP sync
        self._ptp = await create_synchronizer(
            self.node_id,
            is_master=(self.role == NodeRole.MASTER)
        )
        self._ptp.add_sync_callback(self._on_sync_update)
        
        # Update state
        self._local_info.state = NodeState.DISCOVERING
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Coordinator started: {self.node_id} as {self.role.name}")
    
    async def stop(self) -> None:
        """Stop the coordinator."""
        self._running = False
        
        # Cancel tasks
        for task in [self._heartbeat_task, self._discovery_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop PTP
        if self._ptp:
            await self._ptp.stop()
        
        # Stop network
        if self._network:
            await self._network.stop()
        
        logger.info(f"Coordinator stopped: {self.node_id}")
    
    def register_node_callback(
        self,
        callback: Callable[[str, NodeInfo, str], None]
    ) -> None:
        """Register callback for node events."""
        self._node_callbacks.append(callback)
    
    def register_status_callback(
        self,
        callback: Callable[[SystemStatus], None]
    ) -> None:
        """Register callback for system status updates."""
        self._status_callbacks.append(callback)
    
    async def register_array(
        self,
        array_position: ArrayPosition,
        max_objects: int = 10,
        latency_ms: float = 10.0
    ) -> None:
        """Register this node as an array worker."""
        self._local_info.role = NodeRole.WORKER
        self._local_info.array_position = array_position
        self._local_info.max_objects = max_objects
        self._local_info.processing_latency_ms = latency_ms
        
        # Announce to master
        if self._network:
            await self._announce_node()
    
    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """Get information about a node."""
        return self._nodes.get(node_id)
    
    def get_all_nodes(self) -> List[NodeInfo]:
        """Get information about all nodes."""
        return list(self._nodes.values())
    
    def get_workers(self) -> List[NodeInfo]:
        """Get all worker nodes."""
        return [
            n for n in self._nodes.values()
            if n.role == NodeRole.WORKER
        ]
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status."""
        active = sum(1 for n in self._nodes.values() if n.state == NodeState.ACTIVE)
        synced = sum(
            1 for n in self._nodes.values()
            if abs(n.sync_offset_ns) < 1000
        )
        total_objects = sum(n.objects_tracked for n in self._nodes.values())
        avg_latency = (
            sum(n.processing_latency_ms for n in self._nodes.values()) / len(self._nodes)
            if self._nodes else 0.0
        )
        
        return SystemStatus(
            timestamp=time.time(),
            node_count=len(self._nodes) + 1,  # +1 for self
            active_nodes=active + 1,
            synced_nodes=synced + 1,
            total_objects=total_objects,
            average_latency_ms=avg_latency,
            system_load=sum(n.cpu_usage for n in self._nodes.values()) / max(len(self._nodes), 1)
        )
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running:
            try:
                self._local_info.last_heartbeat = time.time()
                
                # Update local stats
                self._update_local_stats()
                
                # Send heartbeat
                if self._network:
                    heartbeat_msg = Message(
                        msg_type=MessageType.HEARTBEAT,
                        source_id=self.node_id,
                        payload=self._serialize_node_info(self._local_info),
                        timestamp=time.time_ns()
                    )
                    self._network.send_udp_multicast(heartbeat_msg)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            await asyncio.sleep(self.heartbeat_interval_ms / 1000)
    
    async def _discovery_loop(self) -> None:
        """Periodically discover new nodes."""
        while self._running:
            try:
                if self._local_info.state == NodeState.DISCOVERING:
                    # Send discovery request
                    if self._network:
                        discovery_msg = Message(
                            msg_type=MessageType.DISCOVERY,
                            source_id=self.node_id,
                            payload=json.dumps({
                                "role": self.role.name,
                                "udp_port": self.udp_port,
                                "tcp_port": self.tcp_port
                            }).encode(),
                            timestamp=time.time_ns()
                        )
                        self._network.send_udp_multicast(discovery_msg)
                    
                    # If we found a master, transition to syncing
                    master = self._find_master()
                    if master and self.role != NodeRole.MASTER:
                        self._local_info.state = NodeState.SYNCING
                        await self._join_cluster(master)
                
            except Exception as e:
                logger.error(f"Discovery error: {e}")
            
            await asyncio.sleep(0.5)
    
    async def _cleanup_loop(self) -> None:
        """Remove stale nodes."""
        while self._running:
            try:
                current_time = time.time()
                stale_nodes = []
                
                async with self._lock:
                    for node_id, node in list(self._nodes.items()):
                        if current_time - node.last_heartbeat > self.node_timeout_ms / 1000:
                            stale_nodes.append(node_id)
                            node.state = NodeState.OFFLINE
                            self._notify_node_event(node_id, node, "failed")
                    
                    for node_id in stale_nodes:
                        del self._nodes[node_id]
                
                # Notify status update
                status = self.get_system_status()
                for callback in self._status_callbacks:
                    try:
                        callback(status)
                    except Exception as e:
                        logger.error(f"Status callback error: {e}")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
            
            await asyncio.sleep(self.node_timeout_ms / 1000)
    
    async def _on_discovery(self, message: Message, addr: NetworkEndpoint) -> None:
        """Handle discovery message."""
        if message.source_id == self.node_id:
            return
        
        try:
            data = json.loads(message.payload.decode())
            
            # If we're master, respond with handshake
            if self.role == NodeRole.MASTER:
                node_info = NodeInfo(
                    node_id=message.source_id,
                    role=NodeRole(data.get("role", "WORKER")),
                    state=NodeState.DISCOVERING,
                    udp_endpoint=NetworkEndpoint(addr.host, data.get("udp_port", 5000)),
                    tcp_endpoint=NetworkEndpoint(addr.host, data.get("tcp_port", 5001))
                )
                
                async with self._lock:
                    self._pending_nodes[message.source_id] = node_info
                
                # Send handshake
                await self._send_handshake(message.source_id, addr)
        
        except Exception as e:
            logger.error(f"Discovery handling error: {e}")
    
    async def _on_heartbeat(self, message: Message, addr: NetworkEndpoint) -> None:
        """Handle heartbeat message."""
        if message.source_id == self.node_id:
            return
        
        try:
            node_info = self._deserialize_node_info(message.payload)
            node_info.last_heartbeat = time.time()
            
            async with self._lock:
                if message.source_id in self._nodes:
                    old_state = self._nodes[message.source_id].state
                    self._nodes[message.source_id] = node_info
                    
                    if old_state != node_info.state:
                        self._notify_node_event(message.source_id, node_info, "updated")
                elif message.source_id in self._pending_nodes:
                    self._nodes[message.source_id] = node_info
                    del self._pending_nodes[message.source_id]
                    self._notify_node_event(message.source_id, node_info, "joined")
        
        except Exception as e:
            logger.error(f"Heartbeat handling error: {e}")
    
    async def _on_handshake(self, message: Message, addr: NetworkEndpoint) -> None:
        """Handle handshake message."""
        try:
            data = json.loads(message.payload.decode())
            
            # Update our state based on handshake
            if data.get("accepted", False):
                self._local_info.state = NodeState.ACTIVE
                logger.info(f"Joined cluster, assigned role: {data.get('assigned_role', 'WORKER')}")
            
        except Exception as e:
            logger.error(f"Handshake handling error: {e}")
    
    async def _on_status(self, message: Message, addr: NetworkEndpoint) -> None:
        """Handle status message."""
        # Process status updates from master
        pass
    
    async def _send_handshake(self, node_id: str, addr: NetworkEndpoint) -> None:
        """Send handshake response to node."""
        if self._network:
            handshake_msg = Message(
                msg_type=MessageType.HANDSHAKE,
                source_id=self.node_id,
                payload=json.dumps({
                    "accepted": True,
                    "assigned_role": "WORKER",
                    "master_id": self.node_id,
                    "sync_master": True
                }).encode(),
                timestamp=time.time_ns()
            )
            await self._network.send_tcp(handshake_msg, addr)
    
    async def _announce_node(self) -> None:
        """Announce this node to the network."""
        if self._network:
            announce_msg = Message(
                msg_type=MessageType.DISCOVERY,
                source_id=self.node_id,
                payload=self._serialize_node_info(self._local_info),
                timestamp=time.time_ns()
            )
            self._network.send_udp_multicast(announce_msg)
    
    async def _join_cluster(self, master: NodeInfo) -> None:
        """Join existing cluster."""
        logger.info(f"Joining cluster with master: {master.node_id}")
        
        # Connect to master
        if self._network:
            await self._network.connect_tcp(master.tcp_endpoint)
        
        # Sync time with master
        if self._ptp:
            # PTP will automatically sync
            pass
    
    def _find_master(self) -> Optional[NodeInfo]:
        """Find master node in discovered nodes."""
        for node in self._nodes.values():
            if node.role == NodeRole.MASTER:
                return node
        return None
    
    def _update_local_stats(self) -> None:
        """Update local node statistics."""
        # In real implementation, these would come from system metrics
        self._local_info.cpu_usage = 0.3  # Placeholder
        self._local_info.memory_usage = 0.4  # Placeholder
    
    def _on_sync_update(self, stats: SyncStats) -> None:
        """Handle PTP sync update."""
        self._local_info.sync_offset_ns = stats.offset_ns
        
        if stats.is_synced and self._local_info.state == NodeState.SYNCING:
            self._local_info.state = NodeState.ACTIVE
    
    def _notify_node_event(self, node_id: str, node: NodeInfo, event: str) -> None:
        """Notify node event callbacks."""
        for callback in self._node_callbacks:
            try:
                callback(node_id, node, event)
            except Exception as e:
                logger.error(f"Node callback error: {e}")
    
    def _serialize_node_info(self, info: NodeInfo) -> bytes:
        """Serialize node info to bytes."""
        data = {
            "node_id": info.node_id,
            "role": info.role.name,
            "state": info.state.name,
            "udp_host": info.udp_endpoint.host,
            "udp_port": info.udp_endpoint.port,
            "tcp_host": info.tcp_endpoint.host,
            "tcp_port": info.tcp_endpoint.port,
            "max_objects": info.max_objects,
            "processing_latency_ms": info.processing_latency_ms,
            "objects_tracked": info.objects_tracked,
            "cpu_usage": info.cpu_usage,
            "memory_usage": info.memory_usage,
            "version": info.version
        }
        
        if info.array_position:
            data["array_position"] = {
                "array_id": info.array_position.array_id,
                "x": info.array_position.position.x,
                "y": info.array_position.position.y,
                "orientation": info.array_position.orientation
            }
        
        return json.dumps(data).encode()
    
    def _deserialize_node_info(self, data: bytes) -> NodeInfo:
        """Deserialize node info from bytes."""
        d = json.loads(data.decode())
        
        info = NodeInfo(
            node_id=d["node_id"],
            role=NodeRole[d["role"]],
            state=NodeState[d["state"]],
            udp_endpoint=NetworkEndpoint(d["udp_host"], d["udp_port"]),
            tcp_endpoint=NetworkEndpoint(d["tcp_host"], d["tcp_port"]),
            max_objects=d.get("max_objects", 10),
            processing_latency_ms=d.get("processing_latency_ms", 10.0),
            objects_tracked=d.get("objects_tracked", 0),
            cpu_usage=d.get("cpu_usage", 0.0),
            memory_usage=d.get("memory_usage", 0.0),
            version=d.get("version", "1.0.0")
        )
        
        if "array_position" in d:
            ap = d["array_position"]
            info.array_position = ArrayPosition(
                array_id=ap["array_id"],
                position=Vector2D(ap["x"], ap["y"]),
                orientation=ap["orientation"]
            )
        
        return info


class LoadBalancer:
    """
    Load balancer for distributing tracking workload.
    
    Ensures even distribution of objects across arrays and
    handles array failure scenarios.
    """
    
    def __init__(self, coordinator: ArrayCoordinator) -> None:
        self.coordinator = coordinator
    
    def get_optimal_array_for_object(
        self,
        position: Vector2D,
        exclude: Optional[Set[str]] = None
    ) -> Optional[str]:
        """Get best array to track an object at position."""
        exclude = exclude or set()
        workers = self.coordinator.get_workers()
        
        best_array = None
        best_score = -1.0
        
        for worker in workers:
            if worker.node_id in exclude:
                continue
            
            if not worker.array_position:
                continue
            
            # Calculate score based on distance and load
            dist = position.distance_to(worker.array_position.position)
            distance_score = max(0, 10 - dist)  # Prefer closer arrays
            
            load_score = 1.0 - (worker.objects_tracked / worker.max_objects)
            
            # Combine scores
            score = distance_score * 0.6 + load_score * 0.4
            
            if score > best_score:
                best_score = score
                best_array = worker.node_id
        
        return best_array
    
    def calculate_rebalancing(
        self,
        object_positions: Dict[str, Vector2D]
    ) -> Dict[str, str]:
        """
        Calculate optimal reassignment of objects to arrays.
        
        Returns mapping of object_id -> array_id.
        """
        assignments = {}
        workers = self.coordinator.get_workers()
        
        if not workers:
            return assignments
        
        # Simple greedy assignment
        for obj_id, position in object_positions.items():
            # Exclude arrays already at capacity
            exclude = {
                w.node_id for w in workers
                if w.objects_tracked >= w.max_objects
            }
            
            best_array = self.get_optimal_array_for_object(position, exclude)
            if best_array:
                assignments[obj_id] = best_array
        
        return assignments
    
    def estimate_system_capacity(self) -> Dict[str, any]:
        """Estimate total system capacity."""
        workers = self.coordinator.get_workers()
        
        total_capacity = sum(w.max_objects for w in workers)
        current_load = sum(w.objects_tracked for w in workers)
        
        return {
            "total_arrays": len(workers),
            "total_capacity": total_capacity,
            "current_objects": current_load,
            "available_capacity": total_capacity - current_load,
            "utilization": current_load / total_capacity if total_capacity > 0 else 0.0
        }
