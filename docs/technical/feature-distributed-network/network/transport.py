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
