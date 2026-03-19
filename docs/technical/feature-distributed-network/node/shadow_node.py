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
