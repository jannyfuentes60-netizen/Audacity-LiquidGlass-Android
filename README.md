# Audacity Liquid Glass Android

An Android-focused porting project based on **Audacity 3.7.8**, with a Flutter interface styled using **LiqKit / liqkit_ui** and a native audio-engine integration layer.

> This repository is independent from La Chamba Audio Lab. No code or assets from that project belong here.

## Project goals

- Use Audacity **3.7.8** as the functional reference and engine source.
- Rebuild the application interface in Flutter; the desktop wxWidgets interface is not directly embeddable in Flutter.
- Use `liqkit_ui` for the Liquid Glass visual system, after validating its Android rendering and performance.
- Preserve Audacity workflows and capabilities wherever the underlying engine and Android platform permit.
- Provide an in-app audio library backed by Android MediaStore. Ask for audio permission when needed, then list accessible audio without opening the system file browser.
- Open media through content URIs and stream/read data as needed rather than copying every audio file into app memory.

## Architecture (target)

- **Flutter UI:** navigation, editing workspace, tracks, toolbars, menus, dialogs, preferences and effect controls.
- **LiqKit layer:** glass surfaces, controls, sheets, menus and motion.
- **Android platform layer (Kotlin):** runtime permission handling, MediaStore queries, content URI access and audio-device/platform integration.
- **Audacity engine bridge (C/C++):** a carefully scoped native interface for project, track, selection, transport, import/export and effect operations.
- **Compatibility inventory:** a tracked list of Audacity 3.7.8 menus, commands, effects, formats and preferences, each marked for Android feasibility and implementation status.

## Audio library and permissions

- Android 13 and newer: request `READ_MEDIA_AUDIO`.
- Android 12 and older: request `READ_EXTERNAL_STORAGE` where applicable.
- Request access only when the user first opens the library and permission is not already granted.
- Query accessible, indexed shared audio through MediaStore; do not request broad all-files access.
- Show permission-denied and empty-library states clearly, and support refreshing the list.
- MediaStore does not expose every private app file or every unindexed location. A separate user-selected URI flow may be needed for those cases.

## Important engineering constraints

Audacity 3.7.8 is a desktop application built around wxWidgets and a large native dependency set. A Flutter Android app cannot simply run the Windows executable or reuse the desktop UI. The port must rebuild the UI and validate which engine modules and dependencies can compile and operate on Android.

“Feature parity” is a goal, not a claim that every desktop feature is already portable. Each feature must be audited and tested. Android-specific interaction, audio routing, background limits, memory constraints and screen size may require adapted workflows.

## Initial milestones

1. Pin and audit the Audacity 3.7.8 source tree, license notices, build system and dependencies.
2. Build a feature/portability inventory from the 3.7.8 menus, commands, effects, import/export formats and preferences.
3. Create the Flutter Android shell and validate the selected LiqKit package on Android.
4. Implement the MediaStore library and permission lifecycle.
5. Define a minimal, stable C ABI/JNI bridge and prove one real engine operation end-to-end.
6. Expand the bridge and Flutter screens incrementally, with tests for each capability.

## Current status

Repository bootstrap and technical validation. No claim is made yet that the Audacity engine builds on Android or that full desktop feature parity has been achieved.

## References

- Audacity 3.7.8 release notes: https://www.audacityteam.org/changelog/3.7.8/
- LiqKit Flutter package: https://pub.dev/packages/liqkit_ui
- Android MediaStore: https://developer.android.com/training/data-storage/shared/media
