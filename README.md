# Audacity 4.0.2 for Android

This branch changes the Android execution strategy. Instead of compiling every Audacity desktop dependency against the Android NDK, it reuses the Android/Linux compatibility layer from Andacious and replaces the Audacity program launched inside its Debian ARM64 environment with the official Audacity 4.0.2 AArch64 AppImage.

## Intended architecture

- **Android shell and compatibility layer:** Andacious (UserLAnd, Debian ARM64, VNC-based desktop display, touch/keyboard forwarding and storage integration).
- **Actual editor:** official Audacity 4.0.2 Linux ARM64 build. The old Audacity package is not the editor target.
- **First launch:** download the 4.0.2 AArch64 AppImage, verify it against the release checksums, extract it (so FUSE is not required), and launch its original AppRun.
- **Interface and engine:** the original Audacity 4.0.2 desktop application, not a recreated editor UI.

Andacious is a compatibility/runtime layer; it is not a separate audio engine. The plan is to reuse the Android/Linux execution infrastructure and replace the application running inside it.

## Important distinction

This is **not a native Qt-for-Android port**. It runs the Linux ARM64 desktop build inside Andacious' Linux environment and displays it through the existing Android remote-desktop layer. This is a much more practical route to test first, but touch ergonomics, audio routing, storage access, performance and lifecycle still need physical-device validation.

## Build

The port/andacious-audacity-4 branch builds the Android wrapper APK from the Andacious source submodule. The preparation step also supplies the publicly available UserLAndLibrary source mirror required by the Andacious project and applies the small API compatibility changes needed by that mirror.

The APK build is not considered successful until GitHub Actions produces a real APK. The runtime is not considered verified until Audacity 4.0.2 launches and passes audio/file workflow tests on an Android device.

## Licensing

Audacity is GPLv3. Andacious and UserLAnd components have their own open-source notices and licenses. Keep upstream notices and source references intact when modifying or distributing the combined application.
