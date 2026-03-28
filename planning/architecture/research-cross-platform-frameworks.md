# Cross-Platform Framework Research: Local AI/CV Applications

**Date:** 2026-03-27  
**Scope:** Performance-focused comparison for real-time computer vision with TensorFlow Lite  
**Target Use Case:** Chess Vision App - automatic board detection, 30fps+ camera pipeline, sub-100ms inference

---

## Executive Summary

| Framework | FPS Capability | TFLite Integration | Developer Velocity | Risk Level |
|-----------|----------------|-------------------|--------------------|------------|
| **React Native + VisionCamera** | 30-60 FPS | Excellent (plugins) | Fast | Medium |
| **Flutter (tflite_flutter)** | 30-60 FPS | Good (native binding) | Fast | Low |
| **Native (Swift/Kotlin)** | 60-120 FPS | Native | Slow | Low |

**Recommendation:** Start with Flutter for ML-heavy CV work, React Native acceptable if team stronger in JS.

---

## 1. React Native + VisionCamera

### Architecture
```
Camera Stream → Native Frame Buffer → Frame Processor Plugin → TFLite → JS Layer

Key libraries:
- react-native-vision-camera (v4+)
- react-native-worklets-core (JS thread isolation)
- react-native-fast-tflite or custom plugin
```

### Frame Pipeline (VisionCamera v4)
VisionCamera's **Frame Processors** run at 60+ FPS using:
- Worklet-based JS execution (separate thread)
- Direct native frame access before JS bridge
- Plugin architecture for ML inference

### Pros
✅ **Fast development** - JavaScript/TypeScript only  
✅ **Mature ecosystem** - Large community, many packages  
✅ **VisionCamera v4** - Specifically designed for ML pipelines  
✅ **Hot reload** - Fast iteration cycles  
✅ **Native module escape hatch** - Can write native plugins when needed  

### Cons
⚠️ **Bridge overhead** - For large tensors (e.g., camera frames), must pass through native bridge unless using plugins  
⚠️ **Frame processor complexity** - Custom ML requires native plugin development  
⚠️ **Threading complexity** - Worklets require 'worklet' directive, harder to debug  
⚠️ **TFLite specific integration** - Requires either:
  - `react-native-tflite` (limited, older)
  - `react-native-fast-tflite` (better but newer)
  - Custom native module (most flexible)

### Performance Characteristics
| Metric | Typical Value |
|--------|--------------|
| Camera access latency | <50ms |
| Frame processing (with plugin) | 30-60 FPS |
| TFLite inference time* | 20-100ms depending on model |
| JS Bridge penalty (if used) | 16-33ms (1-2 frames) |

*Inference time is model-dependent; framework overhead is minimal with proper architecture.

### Real-World CV Performance
Based on VisionCamera docs and community:
- Object detection at 60 FPS: ✅ Achievable
- Face detection: ✅ 60+ FPS on modern devices
- Custom TFLite models: ✅ With custom plugin

### Code Pattern
```javascript
const frameProcessor = useFrameProcessor((frame) => {
  'worklet'; // Runs on separate thread
  const detections = detectChessBoard(frame); // Native plugin
  // ... process results
}, []);
```

---

## 2. Flutter (tflite_flutter)

### Architecture
```
Camera Stream → dart:ffi → C++ bindings → TFLite C API → Dart Layer

Key libraries:
- camera (official package)
- tflite_flutter (FFI bindings)
- tflite_flutter_helper (image processing)
```

### Frame Pipeline
- Direct FFI (Foreign Function Interface) bindings - no bridge
- Memory sharing between Dart and native code
- Isolate-based threading for inference

### Pros
✅ **Best ML integration** - FFI is more direct than RN bridge  
✅ **Type-safe** - Dart's type system reduces runtime errors  
✅ **Single codebase compiled** - AOT compilation to native code  
✅ **Growing ML ecosystem** - tflite_flutter actively maintained  
✅ **Performance** - Closer to native than RN  
✅ **Hot reload** - Fast development cycle  

### Cons
⚠️ **Learning curve** - Dart is less common than JS  
⚠️ **Smaller ecosystem** - Fewer packages than RN (but growing)  
⚠️ **Camera package limitations** - Official camera package works but plugin ecosystem smaller  
⚠️ **Platform channels for advanced features** - Still needed for some native features  

### Performance Characteristics
| Metric | Typical Value |
|--------|--------------|
| Camera access latency | <50ms |
| Frame processing (Isolate) | 30-60 FPS |
| TFLite inference time* | 20-100ms (same as RN) |
| FFI overhead | ~1-2ms (negligible) |

### Key Advantage: FFI vs Bridge
- **Flutter FFI:** Direct memory access, zero-copy possible
- **React Native bridge:** Serialized JSON, significant overhead for large data
- **Result:** Flutter ~2-3x faster for image/frame data transfer

### Real-World CV Performance
- tflite_flutter reports 30+ FPS for real-time classification
- Direct bitmap access through FFI means less overhead
- Better suited for per-frame inference loops

### Code Pattern
```dart
final interpreter = Interpreter.fromFile(modelFile);
// Run on separate isolate
await Isolate.run(() {
  interpreter.run(input, output);
});
```

---

## 3. Native (Swift/Kotlin)

### Architecture
```
Camera Stream → AVFoundation/Camera2 → TFLite Java/Swift API → UI

Key libraries:
- TFLite Swift/ObjC++ (iOS)
- TFLite Java (Android)
- Camera APIs (native)
```

### Frame Pipeline
- Native camera APIs (fastest access)
- Direct TFLite integration
- Zero bridge/FFI overhead

### Pros
✅ **Maximum performance** - No framework overhead  
✅ **Full hardware access** - All camera features, ML accelerators  
✅ **Best TFLite support** - First-class GPU delegate, CoreML delegate  
✅ **Production-grade** - Most stable for ML apps  
✅ **App store optimization** - Native apps often reviewed better  

### Cons
⚠️ **Two codebases** - iOS and Android diverge  
⚠️ **Slowest development** - No hot reload, harder iteration  
⚠️ **Expertise required** - Need Swift AND Kotlin skills  
⚠️ **Maintenance cost** - Twice the bugs, twice the updates  

### Performance Characteristics
| Metric | Typical Value |
|--------|--------------|
| Camera access latency | <10ms (fastest) |
| Frame processing | 60-120 FPS |
| TFLite inference time* | 15-80ms (faster delegates) |
| Bridge/FFI overhead | None |

### Real-World CV Performance
- **60-120 FPS** on modern devices
- **GPU/Coral delegate** access for <20ms inference
- CameraX/Camera2 full feature utilization

---

## Comparison Matrix

| Factor | React Native | Flutter | Native |
|--------|--------------|---------|--------|
| **Dev Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **CV Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **TFLite Integration** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Team Fit (JS)** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Long-term Risk** | Medium | Low | Low |
| **Package Ecosystem** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Learning Curve** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Specific Recommendations for Chess Vision App

### Board Detection Pipeline Requirements
1. **Camera at 30 FPS** - All frameworks viable
2. **TFLite model loading** - Fast on all frameworks
3. **Frame-to-tensor conversion** - Most critical bottleneck
4. **Real-time overlay rendering** - Canvas/Skia both good

### React Native Path
**Best if:**
- Team deeply invested in JS/TS
- Can accept 30 FPS (sufficient for chess)
- Willing to build/write custom native plugin for frame processing

**Implementation:**
1. Use `react-native-vision-camera` v4
2. Create custom frame processor plugin in Swift/Kotlin
3. Do TFLite inference in native plugin, pass minimal results to JS
4. Render overlays with react-native-skia or native view

**Expected perf:** 30 FPS sustained on iPhone 12+/Pixel 6+

### Flutter Path
**Best if:**
- Team willing to learn Dart
- Want best balance of dev speed and performance
- CV is central feature (not bolted on)

**Implementation:**
1. Use official `camera` package
2. `tflite_flutter` with FFI bindings
3. Run inference on separate Isolate
4. Render overlays with Flutter's built-in canvas

**Expected perf:** 30-45 FPS sustained, better memory efficiency

### Native Path
**Best if:**
- Performance is critical (e.g., need 60+ FPS)
- Have native iOS/Android expertise
- Building MVP-proof product

**Hybrid Approach:**
- Start with Flutter/RN for MVP
- Profile actual performance bottlenecks
- Migrate only inference pipeline to native if needed

---

## Decision Framework

```
Is your team strong in JavaScript? 
├─ Yes → React Native (acceptable, but write native plugin)
└─ No → Continue

Is learning Dart acceptable?
├─ Yes → Flutter (best balanced choice for ML app)
└─ No → Continue

Need absolute max performance?
├─ Yes → Native (but accept two codebases)
└─ No → React Native (escape hatch available)
```

### Recommendation
**Flutter** for chess vision app:
1. FFI gives better ML integration than RN bridge
2. Still single codebase
3. Growing ecosystem specifically around on-device ML
4. Performance overhead negligible for 30 FPS target

**React Native is viable** if team can't/won't learn Dart, but requires native plugin work for optimal performance.

---

## References

1. VisionCamera Frame Processors - https://react-native-vision-camera.com/docs/guides/frame-processors
2. tflite_flutter package - https://pub.dev/packages/tflite_flutter
3. TensorFlow Lite mobile performance best practices
4. Comparative studies: Flutter FFI vs React Native bridge overhead

---

**Research by:** Trace  
**Next Steps:** Prototype decision - spike both frameworks with actual TFLite model loading
