# Android port status

Last updated: 2026-11-11

## Target

Official **Audacity 4.0.2**, preserving the upstream Qt interface and real engine. The project is no longer targeting a Flutter recreation.

## Status definitions

- **Not audited:** source or dependency has not yet been inspected.
- **Investigating:** Android feasibility is being evaluated.
- **Prototype:** a proof of concept exists but is not production-ready.
- **Implemented:** connected to upstream Audacity code and Android platform code.
- **Verified:** tested end-to-end on a physical Android device.
- **Blocked:** a documented platform or dependency constraint prevents implementation.
- **Adapted:** a desktop interaction has a documented Android equivalent while preserving the underlying Audacity command.

## Compatibility inventory

| Area | Required outcome | Status |
|---|---|---|
| Upstream source | Pin Audacity 4.0.2 and all submodules | Not audited |
| Qt application | Build original Qt interface for Android | Investigating |
| CMake/dependencies | Resolve Android toolchain and unsupported dependencies | Not audited |
| Home/projects | Preserve Audacity 4 Home screen and project workflows | Not audited |
| Tracks and clips | Preserve upstream track/clip model and editing commands | Not audited |
| Timeline | Preserve selection, zoom, navigation, snapping and playhead behavior | Not audited |
| Transport | Playback, seek, loop and stop | Not audited |
| Recording | Android microphone input, monitoring and latency handling | Not audited |
| Audio setup | Android output/input devices and routing | Not audited |
| Effects | Built-in, realtime and destructive effects | Not audited |
| Generators/analyzers | Preserve available Audacity 4 commands | Not audited |
| Plugins | Audit VST3/LV2/AU assumptions; define Android support honestly | Not audited |
| Projects | Open/save native .aup4 and test .aup3 conversion | Not audited |
| Import/export | Android content URIs, codecs, sample rates and channels | Not audited |
| Android lifecycle | Audio focus, interruptions, background/foreground and memory | Not audited |
| Accessibility | Touch targets, scaling, keyboard and screen-reader behavior | Not audited |

## Architecture rule

Use upstream Audacity 4's Qt application and engine. Android-specific code belongs in narrowly scoped platform adapters and upstream build-system changes. Do not create a second editor UI in Flutter, HTML or a custom widget toolkit.

## First technical gates

1. Pin the Audacity 4.0.2 release source and recursive submodules.
2. Configure Qt for Android and the Android NDK/SDK toolchain.
3. Inventory CMake targets and third-party dependencies; identify desktop-only code.
4. Build a minimal upstream Qt Android application before adding app-specific features.
5. Port audio device enumeration and input/output using Android-supported backends.
6. Verify original interface rendering and touch operation on physical hardware.

## Acceptance rule

A button drawn on screen is not an implementation. A capability is **Implemented** only when it calls the real Audacity 4 code, and **Verified** only after repeatable end-to-end tests on Android.

## Known limitation

Audacity 4.0.2 is officially distributed for desktop platforms; upstream build instructions describe desktop development environments, not an official Android target. This project is an experimental community port, not an official Audacity Android release. Android compatibility must be proven dependency by dependency.
