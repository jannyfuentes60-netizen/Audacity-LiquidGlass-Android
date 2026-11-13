# Android port status

Last updated: 2026-11-13

## Target

Official **Audacity 4.0.2 AArch64**, launched inside the Android/Linux compatibility environment from Andacious. The old Audacity package bundled/installed by the original Andacious configuration is not the target editor.

## Status definitions

- **Not audited:** source or dependency has not yet been inspected.
- **Investigating:** feasibility is being evaluated.
- **Prototype:** a proof of concept exists but is not production-ready.
- **Implemented:** connected to the Android runtime and launch path.
- **Verified:** tested end-to-end on a physical Android device.
- **Blocked:** a documented platform or dependency constraint prevents implementation.

## Compatibility inventory

| Area | Required outcome | Status |
|---|---|---|
| Andacious Android shell | Reuse Android activity, UserLAnd runtime and VNC interaction | Investigating |
| UserLAndLibrary source | Resolve the inaccessible pinned submodule using a compatible source mirror | Investigating |
| Audacity binary | Use official 4.0.2 AArch64 AppImage | Available upstream; third-party plugin support is absent in this ARM64 build |
| AppImage installer | Download, checksum-verify and extract without FUSE | Prototype |
| Original Audacity UI | Launch the actual 4.0.2 Linux application | Not verified |
| Touch and keyboard | Operate the original UI from Android | Not verified |
| Audio output | Route playback through the Android/Linux audio bridge | Not verified |
| Microphone input | Record through Android microphone routing | Not verified |
| Storage | Open/import/export/save through shared Android storage | Not verified |
| Projects | Open/save native .aup4 and verify recovery | Not verified |
| Effects and tools | Verify real Audacity 4 commands | Not verified |
| Android lifecycle | Pause/resume, interruptions and memory behavior | Not verified |

## Architecture rule

Andacious supplies the Android/Linux compatibility layer, not a replacement audio engine. Audacity 4.0.2 remains the actual editor and audio engine. No fake editor UI or substitute waveform engine is allowed.

## Acceptance rule

Do not label the APK successful until CI produces a real APK. Do not label the runtime successful until Audacity 4.0.2 launches on a physical Android device and the audio/file workflows are tested.
