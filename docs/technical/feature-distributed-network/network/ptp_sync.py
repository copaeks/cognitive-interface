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
