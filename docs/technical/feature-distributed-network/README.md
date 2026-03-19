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
