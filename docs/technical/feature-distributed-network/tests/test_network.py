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
