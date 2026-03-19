"""
Synthetic Dataset Generation for Shadow Intelligence Layer.

Generates training data for intent classification and property prediction
using shadow simulation. Creates realistic shadow patterns for:
- Human hands in various poses
- Tools (screwdrivers, hammers, etc.)
- Generic objects

Includes data augmentation for robustness.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
import json


class ObjectType(Enum):
    """Object type categories."""
    HAND = 0
    TOOL = 1
    OTHER = 2


class GraspState(Enum):
    """Hand grasp states."""
    OPEN = 0
    CLOSED = 1
    PINCHING = 2


class InteractionIntent(Enum):
    """Interaction intent categories."""
    POINTING = 0
    MANIPULATING = 1
    RESTING = 2


class MaterialType(Enum):
    """Material type categories."""
    RIGID = 0
    SOFT = 1
    LIQUID = 2


class SizeCategory(Enum):
    """Size categories."""
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


@dataclass
class ShadowSample:
    """Single synthetic shadow sample with labels."""
    shadow: np.ndarray
    object_type: ObjectType
    grasp_state: GraspState
    interaction_intent: InteractionIntent
    material: MaterialType
    size_category: SizeCategory
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'shadow': self.shadow,
            'object_type': self.object_type.value,
            'grasp_state': self.grasp_state.value,
            'interaction_intent': self.interaction_intent.value,
            'material': self.material.value,
            'size_category': self.size_category.value
        }


class ShadowGenerator:
    """Generates synthetic shadow data for training."""
    
    def __init__(
        self,
        image_size: Tuple[int, int] = (64, 64),
        noise_level: float = 0.05,
        seed: Optional[int] = None
    ) -> None:
        """
        Initialize shadow generator.
        
        Args:
            image_size: Output image dimensions (H, W)
            noise_level: Amount of noise to add (0-1)
            seed: Random seed for reproducibility
        """
        self.image_size = image_size
        self.noise_level = noise_level
        
        if seed is not None:
            np.random.seed(seed)
    
    def generate_hand_shadow(
        self,
        grasp_state: GraspState,
        interaction_intent: InteractionIntent,
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic hand shadow.
        
        Args:
            grasp_state: Hand grasp configuration
            interaction_intent: Type of interaction
            size_category: Size of the hand
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        # Scale based on size category
        scale = {SizeCategory.SMALL: 0.6, SizeCategory.MEDIUM: 0.8, SizeCategory.LARGE: 1.0}[size_category]
        
        # Palm center position
        palm_x = w // 2
        palm_y = h // 2 + int(5 * scale)
        
        # Draw palm (ellipse)
        palm_width = int(25 * scale)
        palm_height = int(20 * scale)
        self._draw_ellipse(shadow, palm_x, palm_y, palm_width, palm_height, 1.0)
        
        # Draw fingers based on grasp state
        if grasp_state == GraspState.OPEN:
            # Extended fingers
            finger_angles = [-30, -10, 10, 30]  # Degrees
            finger_lengths = [int(35 * scale), int(38 * scale), int(36 * scale), int(30 * scale)]
            
            for angle, length in zip(finger_angles, finger_lengths):
                self._draw_finger(shadow, palm_x, palm_y - palm_height//2, angle, length, scale)
        
        elif grasp_state == GraspState.CLOSED:
            # Curled fingers
            finger_angles = [-25, -8, 8, 25]
            for angle in finger_angles:
                self._draw_curled_finger(shadow, palm_x, palm_y - palm_height//2, angle, scale)
        
        elif grasp_state == GraspState.PINCHING:
            # Index and thumb extended, others curled
            self._draw_finger(shadow, palm_x - 5, palm_y - palm_height//2, -15, int(35 * scale), scale)
            self._draw_finger(shadow, palm_x + 5, palm_y - palm_height//2, 20, int(30 * scale), scale)
            # Other fingers curled
            for angle in [-25, 25]:
                self._draw_curled_finger(shadow, palm_x, palm_y - palm_height//2, angle, scale)
        
        # Add interaction intent modifications
        if interaction_intent == InteractionIntent.POINTING:
            # Emphasize one finger (index)
            self._draw_finger(shadow, palm_x - 5, palm_y - palm_height//2, -15, int(45 * scale), scale * 1.2)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def generate_tool_shadow(
        self,
        tool_type: str = "screwdriver",
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic tool shadow.
        
        Args:
            tool_type: Type of tool (screwdriver, hammer, wrench, etc.)
            size_category: Size of the tool
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        scale = {SizeCategory.SMALL: 0.5, SizeCategory.MEDIUM: 0.75, SizeCategory.LARGE: 1.0}[size_category]
        
        center_x = w // 2
        center_y = h // 2
        
        if tool_type == "screwdriver":
            # Handle
            handle_width = int(8 * scale)
            handle_length = int(25 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + handle_length//2,
                handle_width, handle_length, 1.0
            )
            # Shaft
            shaft_width = int(3 * scale)
            shaft_length = int(30 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y - shaft_length//2 - 5,
                shaft_width, shaft_length, 0.9
            )
        
        elif tool_type == "hammer":
            # Handle
            handle_width = int(10 * scale)
            handle_length = int(35 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + 10,
                handle_width, handle_length, 1.0
            )
            # Head
            head_width = int(30 * scale)
            head_height = int(12 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y - 15,
                head_width, head_height, 1.0
            )
        
        elif tool_type == "wrench":
            # Handle
            handle_width = int(8 * scale)
            handle_length = int(30 * scale)
            self._draw_rectangle(
                shadow, center_x, center_y + 5,
                handle_width, handle_length, 1.0
            )
            # Head (C-shape)
            head_size = int(15 * scale)
            self._draw_circle(shadow, center_x, center_y - 15, head_size, 1.0)
            # Cutout
            self._draw_circle(shadow, center_x, center_y - 15, head_size//2, 0.0)
        
        else:  # Generic tool
            length = int(40 * scale)
            width = int(12 * scale)
            self._draw_rectangle(shadow, center_x, center_y, width, length, 1.0)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def generate_object_shadow(
        self,
        object_shape: str = "box",
        size_category: SizeCategory = SizeCategory.MEDIUM
    ) -> np.ndarray:
        """
        Generate a synthetic generic object shadow.
        
        Args:
            object_shape: Shape type (box, sphere, cylinder)
            size_category: Size of the object
        
        Returns:
            2D numpy array representing shadow
        """
        h, w = self.image_size
        shadow = np.zeros((h, w), dtype=np.float32)
        
        scale = {SizeCategory.SMALL: 0.4, SizeCategory.MEDIUM: 0.7, SizeCategory.LARGE: 1.0}[size_category]
        
        center_x = w // 2
        center_y = h // 2
        
        if object_shape == "box":
            width = int(30 * scale)
            height = int(25 * scale)
            self._draw_rectangle(shadow, center_x, center_y, width, height, 1.0)
        
        elif object_shape == "sphere":
            radius = int(18 * scale)
            self._draw_circle(shadow, center_x, center_y, radius, 1.0)
        
        elif object_shape == "cylinder":
            width = int(20 * scale)
            height = int(35 * scale)
            self._draw_ellipse(shadow, center_x, center_y, width, height, 1.0)
        
        else:  # Irregular shape
            # Generate random polygon
            num_points = np.random.randint(5, 9)
            radius = int(20 * scale)
            points = []
            for i in range(num_points):
                angle = 2 * np.pi * i / num_points + np.random.uniform(-0.3, 0.3)
                r = radius * np.random.uniform(0.7, 1.3)
                px = int(center_x + r * np.cos(angle))
                py = int(center_y + r * np.sin(angle))
                points.append((px, py))
            self._draw_polygon(shadow, points, 1.0)
        
        # Add noise
        shadow = self._add_noise(shadow)
        
        return shadow
    
    def _draw_ellipse(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        width: int, height: int,
        intensity: float
    ) -> None:
        """Draw filled ellipse on image."""
        h, w = img.shape
        y, x = np.ogrid[:h, :w]
        mask = ((x - cx) ** 2 / (width/2) ** 2 + (y - cy) ** 2 / (height/2) ** 2) <= 1
        img[mask] = intensity
    
    def _draw_circle(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        radius: int,
        intensity: float
    ) -> None:
        """Draw filled circle on image."""
        h, w = img.shape
        y, x = np.ogrid[:h, :w]
        mask = ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2
        img[mask] = intensity
    
    def _draw_rectangle(
        self,
        img: np.ndarray,
        cx: int, cy: int,
        width: int, height: int,
        intensity: float
    ) -> None:
        """Draw filled rectangle on image."""
        h, w = img.shape
        x1 = max(0, cx - width // 2)
        x2 = min(w, cx + width // 2)
        y1 = max(0, cy - height // 2)
        y2 = min(h, cy + height // 2)
        img[y1:y2, x1:x2] = intensity
    
    def _draw_finger(
        self,
        img: np.ndarray,
        start_x: int, start_y: int,
        angle_deg: float,
        length: int,
        width: float
    ) -> None:
        """Draw a finger extending from a point."""
        angle_rad = np.deg2rad(angle_deg - 90)  # Adjust for image coordinates
        
        finger_width = max(3, int(6 * width))
        
        for i in range(length):
            x = int(start_x + i * np.cos(angle_rad))
            y = int(start_y + i * np.sin(angle_rad))
            self._draw_circle(img, x, y, finger_width // 2, 1.0)
    
    def _draw_curled_finger(
        self,
        img: np.ndarray,
        start_x: int, start_y: int,
        angle_deg: float,
        scale: float
    ) -> None:
        """Draw a curled finger."""
        angle_rad = np.deg2rad(angle_deg - 90)
        length = int(15 * scale)
        
        # First segment (extending)
        for i in range(length):
            x = int(start_x + i * np.cos(angle_rad))
            y = int(start_y + i * np.sin(angle_rad))
            self._draw_circle(img, x, y, max(2, int(5 * scale)), 1.0)
        
        # Second segment (curled back)
        mid_x = int(start_x + length * np.cos(angle_rad))
        mid_y = int(start_y + length * np.sin(angle_rad))
        curl_angle = angle_rad + np.deg2rad(90)
        
        for i in range(int(length * 0.7)):
            x = int(mid_x + i * np.cos(curl_angle))
            y = int(mid_y + i * np.sin(curl_angle))
            self._draw_circle(img, x, y, max(2, int(4 * scale)), 1.0)
    
    def _draw_polygon(
        self,
        img: np.ndarray,
        points: List[Tuple[int, int]],
        intensity: float
    ) -> None:
        """Draw filled polygon on image."""
        from skimage.draw import polygon as sk_polygon
        
        if len(points) < 3:
            return
        
        rows = [p[1] for p in points]
        cols = [p[0] for p in points]
        
        try:
            rr, cc = sk_polygon(rows, cols, shape=img.shape)
            img[rr, cc] = intensity
        except ImportError:
            # Fallback: draw as connected circles
            for i, (x, y) in enumerate(points):
                self._draw_circle(img, x, y, 5, intensity)
                if i > 0:
                    prev_x, prev_y = points[i-1]
                    # Draw line
                    num_steps = max(abs(x - prev_x), abs(y - prev_y))
                    for t in range(num_steps):
                        px = int(prev_x + t * (x - prev_x) / num_steps)
                        py = int(prev_y + t * (y - prev_y) / num_steps)
                        self._draw_circle(img, px, py, 3, intensity)
    
    def _add_noise(self, img: np.ndarray) -> np.ndarray:
        """Add realistic noise to shadow."""
        noise = np.random.normal(0, self.noise_level, img.shape)
        img_noisy = img + noise
        
        # Add slight blur for realism
        from scipy.ndimage import gaussian_filter
        img_noisy = gaussian_filter(img_noisy, sigma=0.5)
        
        # Clip to valid range
        return np.clip(img_noisy, 0, 1).astype(np.float32)


class DatasetGenerator:
    """Generates complete training datasets."""
    
    def __init__(
        self,
        image_size: Tuple[int, int] = (64, 64),
        num_samples: int = 10000,
        train_split: float = 0.8,
        seed: int = 42
    ) -> None:
        """
        Initialize dataset generator.
        
        Args:
            image_size: Size of generated images
            num_samples: Total number of samples to generate
            train_split: Fraction for training set
            seed: Random seed
        """
        self.image_size = image_size
        self.num_samples = num_samples
        self.train_split = train_split
        self.seed = seed
        
        self.shadow_gen = ShadowGenerator(image_size, seed=seed)
    
    def generate_dataset(
        self,
        augment: bool = True,
        augmentation_factor: float = 0.3
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Generate complete dataset with train/val split.
        
        Args:
            augment: Whether to apply data augmentation
            augmentation_factor: Probability of applying each augmentation
        
        Returns:
            Dictionary with 'train' and 'val' keys, each containing:
                - 'X': Input images (N, H, W, 1)
                - 'y_object': Object type labels (N, 3)
                - 'y_grasp': Grasp state labels (N, 3)
                - 'y_interaction': Interaction intent labels (N, 3)
                - 'y_material': Material labels (N, 3)
                - 'y_size': Size category labels (N, 3)
        """
        np.random.seed(self.seed)
        
        samples = []
        
        # Generate samples for each category
        samples_per_type = self.num_samples // 3
        
        # Generate hand samples
        for _ in range(samples_per_type):
            grasp = np.random.choice(list(GraspState))
            intent = np.random.choice(list(InteractionIntent))
            size = np.random.choice(list(SizeCategory))
            
            shadow = self.shadow_gen.generate_hand_shadow(grasp, intent, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.HAND,
                grasp_state=grasp,
                interaction_intent=intent,
                material=MaterialType.SOFT,  # Hands are soft
                size_category=size
            ))
        
        # Generate tool samples
        tool_types = ["screwdriver", "hammer", "wrench", "generic"]
        for _ in range(samples_per_type):
            tool = np.random.choice(tool_types)
            size = np.random.choice(list(SizeCategory))
            
            shadow = self.shadow_gen.generate_tool_shadow(tool, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.TOOL,
                grasp_state=GraspState.OPEN,  # N/A for tools
                interaction_intent=InteractionIntent.RESTING,  # N/A for tools
                material=MaterialType.RIGID,  # Tools are rigid
                size_category=size
            ))
        
        # Generate other object samples
        shapes = ["box", "sphere", "cylinder", "irregular"]
        for _ in range(samples_per_type):
            shape = np.random.choice(shapes)
            size = np.random.choice(list(SizeCategory))
            material = np.random.choice(list(MaterialType))
            
            shadow = self.shadow_gen.generate_object_shadow(shape, size)
            
            samples.append(ShadowSample(
                shadow=shadow,
                object_type=ObjectType.OTHER,
                grasp_state=GraspState.OPEN,
                interaction_intent=InteractionIntent.RESTING,
                material=material,
                size_category=size
            ))
        
        # Shuffle samples
        np.random.shuffle(samples)
        
        # Apply augmentation if requested
        if augment:
            samples = self._augment_samples(samples, augmentation_factor)
        
        # Split into train/val
        split_idx = int(len(samples) * self.train_split)
        train_samples = samples[:split_idx]
        val_samples = samples[split_idx:]
        
        # Convert to arrays
        train_data = self._samples_to_arrays(train_samples)
        val_data = self._samples_to_arrays(val_samples)
        
        return {
            'train': train_data,
            'val': val_data
        }
    
    def _augment_samples(
        self,
        samples: List[ShadowSample],
        factor: float
    ) -> List[ShadowSample]:
        """Apply data augmentation to samples."""
        augmented = []
        
        for sample in samples:
            augmented.append(sample)
            
            # Random rotation
            if np.random.random() < factor:
                from scipy.ndimage import rotate
                angle = np.random.uniform(-30, 30)
                rotated = rotate(sample.shadow, angle, reshape=False, mode='constant')
                augmented.append(ShadowSample(
                    shadow=rotated,
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
            
            # Random scaling
            if np.random.random() < factor:
                from scipy.ndimage import zoom
                scale = np.random.uniform(0.8, 1.2)
                scaled = zoom(sample.shadow, scale, mode='constant')
                # Crop or pad to original size
                h, w = self.image_size
                sh, sw = scaled.shape
                if sh > h or sw > w:
                    start_y = (sh - h) // 2
                    start_x = (sw - w) // 2
                    scaled = scaled[start_y:start_y+h, start_x:start_x+w]
                else:
                    padded = np.zeros((h, w))
                    start_y = (h - sh) // 2
                    start_x = (w - sw) // 2
                    padded[start_y:start_y+sh, start_x:start_x+sw] = scaled
                    scaled = padded
                augmented.append(ShadowSample(
                    shadow=scaled.astype(np.float32),
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
            
            # Random translation
            if np.random.random() < factor:
                from scipy.ndimage import shift
                tx = np.random.randint(-5, 6)
                ty = np.random.randint(-5, 6)
                translated = shift(sample.shadow, (ty, tx), mode='constant')
                augmented.append(ShadowSample(
                    shadow=translated,
                    object_type=sample.object_type,
                    grasp_state=sample.grasp_state,
                    interaction_intent=sample.interaction_intent,
                    material=sample.material,
                    size_category=sample.size_category
                ))
        
        return augmented
    
    def _samples_to_arrays(
        self,
        samples: List[ShadowSample]
    ) -> Dict[str, np.ndarray]:
        """Convert samples to numpy arrays."""
        n = len(samples)
        h, w = self.image_size
        
        X = np.zeros((n, h, w, 1), dtype=np.float32)
        y_object = np.zeros((n, 3), dtype=np.float32)
        y_grasp = np.zeros((n, 3), dtype=np.float32)
        y_interaction = np.zeros((n, 3), dtype=np.float32)
        y_material = np.zeros((n, 3), dtype=np.float32)
        y_size = np.zeros((n, 3), dtype=np.float32)
        
        for i, sample in enumerate(samples):
            X[i, :, :, 0] = sample.shadow
            y_object[i, sample.object_type.value] = 1.0
            y_grasp[i, sample.grasp_state.value] = 1.0
            y_interaction[i, sample.interaction_intent.value] = 1.0
            y_material[i, sample.material.value] = 1.0
            y_size[i, sample.size_category.value] = 1.0
        
        return {
            'X': X,
            'y_object': y_object,
            'y_grasp': y_grasp,
            'y_interaction': y_interaction,
            'y_material': y_material,
            'y_size': y_size
        }
    
    def save_dataset(
        self,
        dataset: Dict[str, Dict[str, np.ndarray]],
        path: str
    ) -> None:
        """Save dataset to disk."""
        np.savez_compressed(
            path,
            X_train=dataset['train']['X'],
            y_object_train=dataset['train']['y_object'],
            y_grasp_train=dataset['train']['y_grasp'],
            y_interaction_train=dataset['train']['y_interaction'],
            y_material_train=dataset['train']['y_material'],
            y_size_train=dataset['train']['y_size'],
            X_val=dataset['val']['X'],
            y_object_val=dataset['val']['y_object'],
            y_grasp_val=dataset['val']['y_grasp'],
            y_interaction_val=dataset['val']['y_interaction'],
            y_material_val=dataset['val']['y_material'],
            y_size_val=dataset['val']['y_size']
        )
        print(f"Dataset saved to {path}")
    
    @staticmethod
    def load_dataset(path: str) -> Dict[str, Dict[str, np.ndarray]]:
        """Load dataset from disk."""
        data = np.load(path)
        
        return {
            'train': {
                'X': data['X_train'],
                'y_object': data['y_object_train'],
                'y_grasp': data['y_grasp_train'],
                'y_interaction': data['y_interaction_train'],
                'y_material': data['y_material_train'],
                'y_size': data['y_size_train']
            },
            'val': {
                'X': data['X_val'],
                'y_object': data['y_object_val'],
                'y_grasp': data['y_grasp_val'],
                'y_interaction': data['y_interaction_val'],
                'y_material': data['y_material_val'],
                'y_size': data['y_size_val']
            }
        }


def generate_synthetic_dataset(
    output_path: str,
    num_samples: int = 10000,
    image_size: Tuple[int, int] = (64, 64),
    seed: int = 42
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Generate and save a synthetic dataset.
    
    Args:
        output_path: Path to save dataset
        num_samples: Number of samples to generate
        image_size: Size of generated images
        seed: Random seed
    
    Returns:
        Generated dataset dictionary
    """
    generator = DatasetGenerator(
        image_size=image_size,
        num_samples=num_samples,
        seed=seed
    )
    
    dataset = generator.generate_dataset(augment=True)
    generator.save_dataset(dataset, output_path)
    
    return dataset


if __name__ == "__main__":
    # Generate example dataset
    dataset = generate_synthetic_dataset(
        output_path="shadow_dataset.npz",
        num_samples=10000,
        image_size=(64, 64),
        seed=42
    )
    
    print(f"Training samples: {len(dataset['train']['X'])}")
    print(f"Validation samples: {len(dataset['val']['X'])}")
