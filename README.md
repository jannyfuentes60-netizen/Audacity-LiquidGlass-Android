# Audacity 4 for Android

This repository is focused on a **native Android port of the official Audacity 4 codebase**.

## Non-negotiable direction

- Use the official **Audacity 4.0.2** source as the application and audio-engine foundation.
- Preserve Audacity's original Qt interface, menus, toolbars, track view, clip editing model, effects, project handling and commands.
- Do not recreate the editor in Flutter, HTML or a custom imitation UI.
- Do not replace Audacity's interface with Liquid Glass. The original Audacity 4 interface is the target.
- Make only platform adaptations required for Android: touch input, screen sizing, Android audio devices, permissions, lifecycle and file access.
- Keep upstream code and license notices intact; document every Android-specific patch.

## Technical direction

Audacity 4 is built on Qt. The Android project must adapt the upstream Qt/CMake application rather than wrap a desktop executable or rebuild its interface in another toolkit.

The official Audacity 4 build instructions currently describe desktop toolchains. Upstream does not provide an official Android build target. This port therefore requires auditing dependencies, adapting unsupported platform components, integrating Qt for Android, adapting audio I/O and validating the original application UI on-device.

## Milestones

1. Pin the official Audacity 4.0.2 source and its submodules.
2. Audit CMake targets and dependencies for Android compatibility.
3. Produce a minimal Qt-for-Android build of the unmodified upstream application shell.
4. Resolve platform blockers without replacing Audacity's UI or editing model.
5. Integrate Android audio input/output, focus, permissions and MediaStore/document URI access.
6. Test project open/save, import/export, transport and editing on a physical Android device.
7. Expand verification across effects, generators, analyzers, plugins and remaining commands.

## Current status

The previous Flutter/LiqKit screen was only a mock interface and did not contain the Audacity engine. It is not the target implementation and must not be presented as a working Audacity port.

The Android port has **not yet been built**. No feature is marked implemented or verified until it works through the real Audacity 4 code on Android.

See [docs/ANDROID_PORT_PLAN.md](docs/ANDROID_PORT_PLAN.md) and [docs/PORTING_STATUS.md](docs/PORTING_STATUS.md).

## Upstream references

- Audacity source: https://github.com/audacity/audacity
- Audacity 4.0.2 release: https://github.com/audacity/audacity/releases/tag/Audacity-4.0.2
- Audacity 4 build guide: https://github.com/audacity/audacity/blob/master/BUILDING.md
- Audacity 4.0 release notes: https://www.audacityteam.org/changelog/4.0.0/
- Qt for Android: https://doc.qt.io/qt-6/android.html

Audacity is open source under GPLv3, with third-party components carrying their own license terms. Preserve all applicable notices and comply with the upstream license when distributing modified builds.
