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
