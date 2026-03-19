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
