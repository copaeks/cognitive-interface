"""
Smartphone Integration Example for Shadow Intelligence Layer.

Demonstrates how to integrate the intelligence layer into a mobile application.
Includes examples for Android (Kotlin) and iOS (Swift) integration.
"""

from __future__ import annotations

import os
import sys
import numpy as np
from typing import Dict, List, Optional, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.intelligence_api import IntelligenceAPI, ShadowIntelligence, classify


class SmartphoneIntegration:
    """
    Example integration for smartphone applications.
    
    This class demonstrates best practices for integrating the
    Shadow Intelligence Layer into mobile apps.
    """
    
    def __init__(
        self,
        models_dir: str = "models/pretrained",
        use_npu: bool = True
    ) -> None:
        """
        Initialize smartphone integration.
        
        Args:
            models_dir: Directory containing TFLite models
            use_npu: Whether to use NPU acceleration if available
        """
        self.models_dir = models_dir
        self.use_npu = use_npu
        
        # Initialize API
        mode = "npu" if use_npu else "auto"
        self.api = IntelligenceAPI(
            intent_model_path=os.path.join(models_dir, "intent_model.tflite"),
            property_model_path=os.path.join(models_dir, "property_model.tflite"),
            mode=mode,
            num_threads=4
        )
        
        # Performance tracking
        self.frame_count = 0
        self.total_latency = 0.0
    
    def process_shadow_frame(
        self,
        shadow_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Process a single shadow frame from camera.
        
        Args:
            shadow_data: Shadow observation (64x64 grayscale)
        
        Returns:
            Dictionary with classification results
        """
        # Run classification
        result = self.api.classify(shadow_data)
        
        # Update stats
        self.frame_count += 1
        self.total_latency += result.inference_time_ms
        
        # Format output for mobile app
        return self._format_result(result)
    
    def _format_result(self, result: ShadowIntelligence) -> Dict[str, Any]:
        """Format result for mobile app consumption."""
        output = {
            "object": {
                "type": result.object_type,
                "confidence": round(result.object_confidence, 3)
            },
            "properties": {
                "material": result.material,
                "material_confidence": round(result.material_confidence, 3),
                "size": result.size_category,
                "size_confidence": round(result.size_confidence, 3)
            },
            "overall_confidence": round(result.overall_confidence, 3),
            "inference_time_ms": round(result.inference_time_ms, 2)
        }
        
        # Add hand-specific info
        if result.is_hand():
            output["hand"] = {
                "grasp_state": result.grasp_state,
                "grasp_confidence": round(result.grasp_confidence, 3) if result.grasp_confidence else None,
                "interaction_intent": result.interaction_intent,
                "interaction_confidence": round(result.interaction_confidence, 3) if result.interaction_confidence else None
            }
        
        return output
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if self.frame_count == 0:
            return {"frames_processed": 0, "average_latency_ms": 0}
        
        return {
            "frames_processed": self.frame_count,
            "average_latency_ms": round(self.total_latency / self.frame_count, 2),
            "current_fps": round(1000 / (self.total_latency / self.frame_count), 1)
        }
    
    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.frame_count = 0
        self.total_latency = 0.0


# Android (Kotlin) Integration Example
ANDROID_KOTLIN_EXAMPLE = '''
// Android Integration Example - Kotlin
// Add to your app's build.gradle:
// implementation 'org.tensorflow:tensorflow-lite:2.14.0'
// implementation 'org.tensorflow:tensorflow-lite-gpu:2.14.0'
// implementation 'org.tensorflow:tensorflow-lite-nnapi:2.14.0'

package com.example.shadowintelligence

import android.content.Context
import android.graphics.Bitmap
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.GpuDelegate
import org.tensorflow.lite.nnapi.NnApiDelegate
import java.nio.ByteBuffer
import java.nio.ByteOrder

class ShadowIntelligenceModel(context: Context) {
    
    private var interpreter: Interpreter? = null
    private val inputSize = 64
    private val numChannels = 1
    
    init {
        // Load model with NPU/GPU acceleration
        val options = Interpreter.Options().apply {
            // Try NNAPI (NPU) first
            addDelegate(NnApiDelegate())
            // Fallback to GPU
            // addDelegate(GpuDelegate())
            setNumThreads(4)
        }
        
        val model = context.assets.open("intent_model.tflite").readBytes()
        interpreter = Interpreter(model, options)
    }
    
    fun classify(shadowBitmap: Bitmap): IntelligenceResult {
        // Preprocess bitmap to input buffer
        val inputBuffer = ByteBuffer.allocateDirect(
            4 * inputSize * inputSize * numChannels
        ).order(ByteOrder.nativeOrder())
        
        // Convert bitmap to grayscale and normalize
        for (y in 0 until inputSize) {
            for (x in 0 until inputSize) {
                val pixel = shadowBitmap.getPixel(x, y)
                val gray = (0.299 * (pixel shr 16 and 0xFF) +
                           0.587 * (pixel shr 8 and 0xFF) +
                           0.114 * (pixel and 0xFF)) / 255.0f
                inputBuffer.putFloat(gray)
            }
        }
        
        // Run inference
        val objectOutput = Array(1) { FloatArray(3) }
        val graspOutput = Array(1) { FloatArray(3) }
        val interactionOutput = Array(1) { FloatArray(3) }
        
        interpreter?.runForMultipleInputsOutputs(
            arrayOf(inputBuffer),
            mapOf(
                0 to objectOutput,
                1 to graspOutput,
                2 to interactionOutput
            )
        )
        
        // Parse results
        return IntelligenceResult(
            objectType = argMax(objectOutput[0]),
            objectConfidence = objectOutput[0].max()!!,
            graspState = argMax(graspOutput[0]),
            graspConfidence = graspOutput[0].max()!!,
            interactionIntent = argMax(interactionOutput[0]),
            interactionConfidence = interactionOutput[0].max()!!
        )
    }
    
    private fun argMax(array: FloatArray): String {
        val labels = arrayOf("hand", "tool", "other")
        return labels[array.indices.maxBy { array[it] } ?: 0]
    }
    
    fun close() {
        interpreter?.close()
    }
}

data class IntelligenceResult(
    val objectType: String,
    val objectConfidence: Float,
    val graspState: String,
    val graspConfidence: Float,
    val interactionIntent: String,
    val interactionConfidence: Float
)
'''


# iOS (Swift) Integration Example
IOS_SWIFT_EXAMPLE = '''
// iOS Integration Example - Swift
// Add to Podfile:
// pod 'TensorFlowLiteSwift'

import TensorFlowLite
import CoreImage

class ShadowIntelligenceModel {
    
    private var interpreter: Interpreter?
    private let inputSize = 64
    
    init?() {
        // Load model
        guard let modelPath = Bundle.main.path(
            forResource: "intent_model",
            ofType: "tflite"
        ) else {
            return nil
        }
        
        // Configure with Core ML delegate for NPU
        var options = Interpreter.Options()
        options.threadCount = 4
        
        // Use Core ML delegate for Apple Neural Engine
        let coreMLOptions = CoreMLDelegate.Options(
            enabledDevices: .neuralEngine
        )
        let coreMLDelegate = CoreMLDelegate(options: coreMLOptions)
        
        do {
            interpreter = try Interpreter(
                modelPath: modelPath,
                options: options,
                delegates: [coreMLDelegate]
            )
            try interpreter?.allocateTensors()
        } catch {
            print("Failed to create interpreter: \\(error)")
            return nil
        }
    }
    
    func classify(shadowImage: CIImage) -> IntelligenceResult? {
        // Resize and convert to grayscale
        guard let resized = resizeImage(shadowImage, to: CGSize(
            width: inputSize,
            height: inputSize
        )) else {
            return nil
        }
        
        // Convert to input data
        guard let inputData = imageToInputData(resized) else {
            return nil
        }
        
        // Run inference
        do {
            try interpreter?.copy(inputData, toInputAt: 0)
            try interpreter?.invoke()
            
            // Get outputs
            let objectOutput = try interpreter!.output(at: 0)
            let graspOutput = try interpreter!.output(at: 1)
            let interactionOutput = try interpreter!.output(at: 2)
            
            // Parse results
            let objectData = objectOutput.data.toArray(type: Float.self)
            let graspData = graspOutput.data.toArray(type: Float.self)
            let interactionData = interactionOutput.data.toArray(type: Float.self)
            
            return IntelligenceResult(
                objectType: argMax(objectData),
                objectConfidence: objectData.max() ?? 0,
                graspState: argMax(graspData),
                graspConfidence: graspData.max() ?? 0,
                interactionIntent: argMax(interactionData),
                interactionConfidence: interactionData.max() ?? 0
            )
        } catch {
            print("Inference failed: \\(error)")
            return nil
        }
    }
    
    private func argMax(_ array: [Float]) -> String {
        let labels = ["hand", "tool", "other"]
        guard let maxIndex = array.enumerated().max(by: { $0.element < $1.element })?.offset else {
            return labels[0]
        }
        return labels[maxIndex]
    }
    
    private func resizeImage(_ image: CIImage, to size: CGSize) -> CIImage? {
        let scaleX = size.width / image.extent.width
        let scaleY = size.height / image.extent.height
        return image.transformed(by: CGAffineTransform(scaleX: scaleX, y: scaleY))
    }
    
    private func imageToInputData(_ image: CIImage) -> Data? {
        // Convert CIImage to grayscale float array
        let context = CIContext()
        guard let cgImage = context.createCGImage(image, from: image.extent) else {
            return nil
        }
        
        let width = cgImage.width
        let height = cgImage.height
        let bytesPerPixel = 4
        let bytesPerRow = bytesPerPixel * width
        let bitsPerComponent = 8
        
        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        
        guard let context = CGContext(
            data: &pixels,
            width: width,
            height: height,
            bitsPerComponent: bitsPerComponent,
            bytesPerRow: bytesPerRow,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return nil
        }
        
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        
        // Convert to grayscale floats
        var floatData = [Float]()
        for y in 0..<height {
            for x in 0..<width {
                let offset = (y * width + x) * 4
                let r = Float(pixels[offset])
                let g = Float(pixels[offset + 1])
                let b = Float(pixels[offset + 2])
                let gray = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                floatData.append(gray)
            }
        }
        
        return floatData.withUnsafeBufferPointer { Data(buffer: $0) }
    }
}

struct IntelligenceResult {
    let objectType: String
    let objectConfidence: Float
    let graspState: String
    let graspConfidence: Float
    let interactionIntent: String
    let interactionConfidence: Float
}

extension Data {
    func toArray<T>(type: T.Type) -> [T] {
        return self.withUnsafeBytes {
            Array($0.bindMemory(to: T.self))
        }
    }
}
'''


# React Native Integration Example
REACT_NATIVE_EXAMPLE = '''
// React Native Integration Example
// Install: npm install react-native-tensorflow-lite

import * as tf from '@tensorflow/tf-react-native';

class ShadowIntelligenceService {
    constructor() {
        this.intentModel = null;
        this.propertyModel = null;
        this.inputSize = 64;
    }
    
    async initialize() {
        // Load models
        this.intentModel = await tf.loadGraphModel(
            'models/intent_model.tflite'
        );
        this.propertyModel = await tf.loadGraphModel(
            'models/property_model.tflite'
        );
    }
    
    async classify(shadowImageData) {
        // Preprocess image
        const input = tf.tidy(() => {
            const image = tf.browser.fromPixels(shadowImageData, 1);
            const resized = tf.image.resizeBilinear(image, [64, 64]);
            const normalized = resized.div(255.0);
            return normalized.expandDims(0);
        });
        
        // Run inference
        const [objectPred, graspPred, interactionPred] = 
            await this.intentModel.predict(input);
        
        // Parse results
        const objectType = this.argMax(await objectPred.data());
        const graspState = this.argMax(await graspPred.data());
        const interactionIntent = this.argMax(await interactionPred.data());
        
        // Cleanup
        input.dispose();
        objectPred.dispose();
        graspPred.dispose();
        interactionPred.dispose();
        
        return {
            objectType,
            graspState,
            interactionIntent
        };
    }
    
    argMax(array) {
        const labels = ['hand', 'tool', 'other'];
        let maxIndex = 0;
        let maxValue = array[0];
        for (let i = 1; i < array.length; i++) {
            if (array[i] > maxValue) {
                maxValue = array[i];
                maxIndex = i;
            }
        }
        return labels[maxIndex];
    }
}

export default new ShadowIntelligenceService();
'''


def print_integration_examples():
    """Print all integration examples."""
    print("="*70)
    print("SMARTPHONE INTEGRATION EXAMPLES")
    print("="*70)
    
    print("\n" + "="*70)
    print("ANDROID (KOTLIN)")
    print("="*70)
    print(ANDROID_KOTLIN_EXAMPLE)
    
    print("\n" + "="*70)
    print("iOS (SWIFT)")
    print("="*70)
    print(IOS_SWIFT_EXAMPLE)
    
    print("\n" + "="*70)
    print("REACT NATIVE")
    print("="*70)
    print(REACT_NATIVE_EXAMPLE)


def demo_integration():
    """Demonstrate smartphone integration."""
    print("\n" + "="*70)
    print("DEMONSTRATING SMARTPHONE INTEGRATION")
    print("="*70)
    
    # Create integration instance
    integration = SmartphoneIntegration(
        models_dir="../models/pretrained",
        use_npu=False  # Use CPU for demo
    )
    
    # Simulate processing frames
    print("\nSimulating 10 shadow frames...")
    
    for i in range(10):
        # Generate dummy shadow frame
        shadow_frame = np.random.rand(64, 64).astype(np.float32)
        
        # Process frame
        result = integration.process_shadow_frame(shadow_frame)
        
        print(f"\nFrame {i+1}:")
        print(f"  Object: {result['object']['type']} ({result['object']['confidence']:.1%})")
        print(f"  Material: {result['properties']['material']}")
        print(f"  Size: {result['properties']['size']}")
        print(f"  Latency: {result['inference_time_ms']:.2f} ms")
    
    # Print performance stats
    stats = integration.get_performance_stats()
    print("\n" + "-"*40)
    print("Performance Statistics:")
    print(f"  Frames processed: {stats['frames_processed']}")
    print(f"  Average latency: {stats['average_latency_ms']:.2f} ms")
    print(f"  Effective FPS: {stats['current_fps']:.1f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        print_integration_examples()
    else:
        demo_integration()
