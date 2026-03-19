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
