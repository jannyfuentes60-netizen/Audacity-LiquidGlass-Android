# Audacity 4.0.2 Android execution plan

## Objective

Run the original Audacity 4.0.2 application and audio engine on Android while reusing Andacious' existing Android/Linux compatibility infrastructure. Do not ship the old Audacity version as the editor and do not recreate Audacity's UI.

## Selected architecture

1. Android app shell and runtime: Andacious.
2. Linux userspace: Debian ARM64 managed by UserLAnd.
3. Desktop display/input: the existing VNC-based display and touch/keyboard forwarding from Andacious.
4. Editor: official Audacity 4.0.2 AArch64 AppImage.
5. AppImage handling: download on first launch, verify using the official release checksum file, extract to the app user's home directory, then execute the extracted AppRun. Extraction avoids requiring FUSE.

## Why this replaces the previous build route

The previous branch attempted to compile the full Audacity dependency graph directly for Android. That repeatedly stopped in desktop-oriented dependencies. The AArch64 Linux release asset allows us to keep the original Audacity program while moving the compatibility boundary to Andacious' Linux runtime.

## Implementation gates

### Gate A — Android runtime build
- Reuse the Andacious Android project and its UserLAnd/VNC integration.
- Keep its runtime responsibilities, but change the visible app identity to Audacity 4.
- Build an ARM64-capable Android APK in CI.

### Gate B — replace the launched editor
- Replace the Andacious launch script so it downloads and verifies Audacity 4.0.2 AArch64.
- Extract the AppImage without FUSE.
- Launch the extracted original Audacity application.
- Do not invoke the Debian repository's older audacity package.

### Gate C — device validation
- Verify the original Audacity 4.0.2 interface appears.
- Verify touch, keyboard, zoom, pan and screen sizing.
- Verify microphone capture, playback, audio routing and latency.
- Verify Android storage access for import/export and project save/open.
- Verify app pause/resume and recovery after interruptions.

### Gate D — feature validation
Test real upstream behavior: multitrack editing, clip operations, undo/redo, transport, recording, effects, generators, analyzers, import/export, project save/reopen and recovery.

## Current constraints

- This is a Linux desktop application running through a compatibility layer, not a native Android Qt build.
- The Andacious repository references a UserLAndLibrary submodule that is not currently publicly fetchable at its pinned URL. The build preparation uses a public historical mirror and adapts the small API differences. This must be treated as a compatibility risk and checked by CI.
- The official AppImage may still need system libraries from Debian. Missing runtime libraries must be resolved based on actual launch logs, not guessed.
- A successful APK build does not prove the AppImage launches or that audio I/O works. Physical-device tests remain mandatory.
