# Audacity 4 Android port plan

## Objective

Run the original Audacity 4 Qt application and its real audio engine on Android. The objective is not to reproduce the UI. Keep upstream widgets, menus, toolbars, workspaces, track/clip views, effect interfaces and command implementations wherever the platform allows.

## Upstream baseline

- Repository: https://github.com/audacity/audacity
- Release baseline: `Audacity-4.0.2`
- Toolkit: Qt 6
- Build system: CMake
- Platform status: upstream release targets desktop operating systems; Android is an experimental port target here.

Pin the release tag and submodules before applying patches. Never silently track a moving branch for a reproducible build.

## Porting strategy

### Gate A — source and build graph

- Clone the official repository recursively at the pinned release.
- Record the exact commit and submodule revisions.
- Configure Qt for Android with a matching Android SDK/NDK toolchain.
- Enumerate CMake targets, compile definitions and third-party dependencies.
- Categorize each dependency: Android-ready, needs configuration, needs a port, or desktop-only.
- Do not replace the upstream Qt UI to get past a dependency failure.

### Gate B — smallest native Qt build

- Create a minimal Android package using Qt's Android deployment flow.
- Bring up the original Audacity Qt application entry point.
- Resolve missing platform abstractions incrementally.
- Verify scaling, orientation, keyboard, touch and lifecycle.
- Do not publish a fake editor shell as an Audacity APK.

### Gate C — audio platform

- Audit upstream audio backends and device abstraction.
- Implement or select Android-compatible capture/playback backends.
- Handle audio focus, route changes, microphone permission, interruptions and app lifecycle.
- Verify latency, sample rates, channel layouts and stable playback/recording.

### Gate D — file and project workflows

- Integrate Android document/content URI access for open/import/export.
- Preserve the upstream project format and save/recovery logic.
- Test .aup4 open/save and .aup3 conversion.
- Avoid broad all-files permission when the Storage Access Framework or MediaStore is sufficient.

### Gate E — feature verification

Test real upstream operations: clip selection and grouping, move/trim/split, undo/redo, transport/seek/loop, recording, effects, generators, analyzers, import/export and project recovery. Record unsupported desktop-only features rather than showing nonfunctional controls.

## Rules

1. The original Audacity 4 interface is the UI source of truth.
2. No Flutter editor, HTML editor, or independently recreated waveform/editor.
3. No mock buttons presented as working functionality.
4. Android adaptations must preserve the underlying Audacity command and project behavior.
5. Each upstream patch must be small, documented and reproducible.
6. Do not label an APK successful until the real native app installs and launches on a physical Android device.
