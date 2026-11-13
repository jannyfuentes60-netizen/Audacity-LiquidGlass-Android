# Flutter library shell

This is the separate Flutter UI layer for the **library and navigation only**.

- Liquid Glass is confined to this Flutter layer.
- Audacity 4.0.2 remains the original Linux desktop application launched inside the Andacious runtime.
- The remote desktop surface must never be wrapped in, tinted by, or painted over with Liquid Glass.
- First launch evaluates Android device information and recommends one of three library-only glass tiers. The choice is persisted and the setup prompt is not shown again.
- Settings can change the tier later.

## Current integration status

This is an initial Flutter UI scaffold, not yet wired into the existing Andacious Android launcher. The `openAudacity` method channel is an explicit integration seam; the native Android host must implement it and hand off to the existing Andacious runtime. The local audio library, Android audio-file picker, and recent-project index are also not connected yet.

## Quality recommendation

The first pass uses Android's low-RAM classification, physical RAM, CPU core count, and Android API level. It does **not** pretend to know the GPU model or benchmark it: a native Vulkan/Impeller capability probe and a short on-device frame-time test are still required before automatically recommending Premium based on GPU performance. The quality selection is saved locally with SharedPreferences.

## Dependency

Liquid Glass is provided by [liquid_glass_widgets](https://pub.dev/packages/liquid_glass_widgets), using its iOS 27 theme preset. The library content remains solid/opaque; glass is reserved for navigation and floating controls.
