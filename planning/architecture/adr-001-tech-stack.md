# Architecture Decision Record: Tech Stack

## Status
**Proposed** - Research complete, awaiting final decision

## Context
CV-001 requires a mobile app platform and ML inference framework for **fully automatic** chess board detection and game recording. The vision: place phone propped next to board, app auto-detects everything, zero manual calibration.

See [research-cross-platform-frameworks.md](./research-cross-platform-frameworks.md) for full performance analysis.

## Decision
**UNDER REVIEW** - Recommending Flutter based on research

## Research Summary

### Frameworks Evaluated
1. **React Native + VisionCamera** - Good, bridge overhead for CV
2. **Flutter (tflite_flutter)** - Best balance for ML workloads
3. **Native (Swift/Kotlin)** - Maximum performance, two codebases

### Key Findings

| Framework | Frame Rate | TFLite Integration | Best For |
|-----------|------------|---------------------|----------|
| **Flutter** | 30-45 FPS | FFI (direct, fast) | ML-centric apps |
| **React Native** | 30-60 FPS | Native plugins needed | Team knows JS well |
| **Native** | 60-120 FPS | Native APIs | Max performance required |

### Critical Insight: FFI vs Bridge
- **Flutter uses FFI** (Foreign Function Interface): Direct memory sharing, negligible overhead
- **React Native uses Bridge**: Serialized JSON, significant overhead for large data (images/frames)
- **Impact:** Flutter is 2-3x faster for frame data transfer, critical for real-time CV

## Recommendation

**Primary Choice:** Flutter + TensorFlow Lite
- **Rationale:** FFI gives best ML integration, single codebase, growing ML ecosystem
- **Expected perf:** 30-45 FPS sustained on modern devices
- **Dev speed:** Hot reload, single language (Dart), good tooling

**Alternative:** React Native + VisionCamera
- **If:** Team cannot learn Dart, deep JS expertise
- **Requirement:** Write custom native plugin for frame processing to avoid bridge overhead
- **Risk:** Higher complexity for CV pipeline

**Escape hatch:** Native modules in either framework if performance insufficient

## Folder Structure
```
app/
├── lib/
│   ├── ai/              # AI model integration (TFLite via FFI)
│   │   ├── inference/   # TFLite model loading
│   │   ├── board/       # Board detection logic (automatic)
│   │   ├── piece/       # Piece classification
│   │   └── tracking/    # Move tracking & state management
│   ├── components/      # Dart/Flutter widgets
│   ├── design/          # UI/UX components, themes
│   └── screens/         # App screens
├── test/                # Unit/integration tests
├── android/             # Android-specific native code (if needed)
├── ios/                 # iOS-specific native code (if needed)
└── assets/              # Images, fonts, models

planning/
├── ai/                  # AI model architecture, training plans
├── app-design/          # UI/UX design system
└── general/             # Standards, rules, glossary
```

## Key Packages (Flutter Path)

| Package | Purpose |
|---------|---------|
| `camera` | Official camera access |
| `tflite_flutter` | TFLite FFI bindings |
| `tflite_flutter_helper` | Image preprocessing |
| `flutter_isolate` | Background inference |

## Evaluation Criteria

1. **Developer velocity** - How fast can we iterate?
2. **Performance** - Can we hit <100ms inference per frame?
3. **Accuracy** - Can we reliably auto-detect board without calibration?
4. **Maintenance** - Long-term supportability
5. **Risk** - Technical unknowns

## Metrics for Decision Validation

Test in Week 1:
- Camera access latency: Target <50ms
- TFLite model load time: Target <500ms
- Real-time frame processing FPS: Target 30+ FPS sustained
- **Auto-board detection success rate (no calibration)**: Target >90%
- **False positive/negative move detection**: Target <5%

## Related Documents
- [Research: Cross-Platform Frameworks](./research-cross-platform-frameworks.md)
- ADR-002: Board Detection Approach (automatic) - *To be written*
- ADR-003: Piece Recognition Strategy - *To be written*
- App prototype spike - *Pending decision*

## Decision Date
**Target:** 2026-03-28 (After review)

## Open Questions

1. Team willing to learn Dart/Flutter? (Blocker if no)
2. MVP timeline - can we budget 1-2 days for framework spike?
3. Need Android only initially, or both platforms from start?

---

**Author:** Trace  
**Stakeholders:** Jan  
**Last Updated:** 2026-03-27
