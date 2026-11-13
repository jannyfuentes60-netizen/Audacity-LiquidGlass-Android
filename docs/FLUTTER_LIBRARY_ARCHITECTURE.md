# Flutter library / Andacious runtime boundary

## Required separation

The Flutter app owns only the library experience: onboarding, local audio browsing, search/sort, recent items, and settings. Its Liquid Glass renderer must not sit over the remote desktop view.

Andacious continues to own the Linux userspace, VNC/remote desktop session, touch and keyboard forwarding, and process lifecycle. Audacity 4.0.2 remains the unmodified upstream desktop editor launched by the existing runtime script.

## Handoff contract

Flutter calls the Android host method channel `com.djfaraon.audacity/runtime` with method `openAudacity`. The Android host must start/resume the Andacious runtime and present its existing remote desktop activity. The remote desktop must be a separate native screen/window, not a Flutter widget layered with glass.

## First-launch quality setup

The Flutter scaffold stores `library_glass_quality_v1` in SharedPreferences. If absent, it inspects Android low-RAM classification, physical RAM, CPU core count and API level, preselects a conservative recommendation, and presents the choice once. Users can change it later in Settings.

This initial assessment does not inspect GPU vendor/driver or run a rendering benchmark. Do not label it a complete hardware benchmark until the native capability probe and frame-time test are implemented.

## Build/integration gates

1. Generate/commit the Flutter Android host and pin a compatible Flutter SDK (the selected Liquid Glass package requires Flutter 3.41+).
2. Implement the native method-channel handoff to Andacious and verify back-stack/lifecycle behavior.
3. Implement Android audio permission handling and a system audio picker for the library.
4. Add GPU/Vulkan/Impeller capability checks and a short frame-time benchmark; recommend Premium only when both device capability and measured frame pacing support it.
5. Keep the Audacity remote desktop entirely outside Flutter's Liquid Glass layer.
