# Porting status and compatibility audit

Last updated: 2026-11-11

This document is the source of truth for porting decisions. A feature is not considered implemented merely because its name appears in the Flutter UI.

## Status definitions

- **Not audited:** source and dependencies have not yet been inspected.
- **Investigating:** implementation and Android constraints are being evaluated.
- **Prototype:** a proof of concept exists but is not production-ready.
- **Implemented:** connected to the real engine/platform implementation.
- **Verified:** covered by repeatable tests on a physical Android device.
- **Blocked:** a documented dependency or platform constraint prevents implementation.
- **Adapted:** the desktop workflow has a documented Android-friendly equivalent.

## Compatibility inventory

| Area | Scope to audit | Status |
|---|---|---|
| Project lifecycle | New, open, save, save as, close, recovery | Not audited |
| Audio I/O | Import, export, codecs, sample rates, channels | Not audited |
| Tracks | Add, remove, reorder, mute, solo, gain, pan | Not audited |
| Editing | Select, cut, copy, paste, trim, split, undo, redo | Not audited |
| Timeline | Zoom, scroll, snapping, selection precision | Not audited |
| Recording | Microphone capture, monitoring, input selection | Not audited |
| Effects | Built-in effects, realtime/non-realtime processing, presets | Not audited |
| Analysis | Analyze menu, measurements, labels and reports | Not audited |
| Automation | Macros, scripting and command execution | Not audited |
| Preferences | Audio, devices, interface, directories and import/export | Not audited |
| Accessibility | Screen readers, scalable text, touch targets | Not audited |
| Android integration | MediaStore, permissions, audio focus, lifecycle | Investigating |

## First technical gates

1. Pin the exact Audacity 3.7.8 source revision and its submodules.
2. Map the native build graph and identify dependencies unavailable or unsupported on Android.
3. Determine which engine components can be built as Android native libraries without the wxWidgets desktop UI.
4. Define a narrow C ABI/JNI proof of concept before designing a broad bridge.
5. Verify LiqKit's package version, Android support, shader behavior and performance on representative devices.
6. Test MediaStore permission and URI behavior on Android 13+ and Android 12 or older.

## Acceptance rule

A capability is only marked **Verified** after an end-to-end test on Android using the actual native implementation. UI mockups, placeholder buttons and desktop-only tests do not count.
