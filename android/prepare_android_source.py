#!/usr/bin/env python3
"""Apply the Android-only compatibility overlay to the pinned Audacity 4.0.2 tree."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream" / "audacity"

def edit(rel, old, new, label):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Missing upstream file for {label}: {path}")
    data = path.read_text(encoding="utf-8")
    if new in data:
        print(f"already patched: {label}")
        return
    if old not in data:
        raise SystemExit(f"Cannot safely patch {label}; upstream context changed: {rel}")
    path.write_text(data.replace(old, new, 1), encoding="utf-8")
    print(f"patched: {label}")

edit(
    "muse/buildscripts/cmake/GetPlatformInfo.cmake",
    r'''if(${CMAKE_CXX_COMPILER} MATCHES "/em\\+\\+(-[a-zA-Z0-9.])?$")
    set(OS_IS_WASM 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Windows")
    set(OS_IS_WIN 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Linux")
    set(OS_IS_LIN 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "FreeBSD")
    set(OS_IS_FBSD 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Darwin")
    set(OS_IS_MAC 1)
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_HOST_SYSTEM_NAME}")
endif()''',
    r'''if(CMAKE_SYSTEM_NAME STREQUAL "Android")
    set(OS_IS_ANDROID 1)
elseif(${CMAKE_CXX_COMPILER} MATCHES "/em\\+\\+(-[a-zA-Z0-9.])?$")
    set(OS_IS_WASM 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Windows")
    set(OS_IS_WIN 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Linux")
    set(OS_IS_LIN 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "FreeBSD")
    set(OS_IS_FBSD 1)
elseif(${CMAKE_HOST_SYSTEM_NAME} MATCHES "Darwin")
    set(OS_IS_MAC 1)
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_HOST_SYSTEM_NAME}")
endif()''',
    "Android target platform detection",
)

edit(
    "muse/buildscripts/cmake/GetPlatformInfo.cmake",
    r'''set(archdetect_c_code "''',
    r'''if(OS_IS_ANDROID)
    if(CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
        set(ARCH_IS_AARCH64 1)
    else()
        message(FATAL_ERROR "Initial Android port supports arm64-v8a only; got: ${CMAKE_ANDROID_ARCH_ABI}")
    endif()
    set(PLATFORM_DETECTED 1)
    return()
endif()

set(archdetect_c_code "''',
    "cross-compile-safe Android ABI detection",
)

edit(
    "muse/buildscripts/cmake/SetupQt6.cmake",
    r'''    list(APPEND qt_components PrintSupport)
    list(APPEND QT_LIBRARIES Qt::PrintSupport)''',
    r'''    if(NOT OS_IS_ANDROID)
        list(APPEND qt_components PrintSupport)
        list(APPEND QT_LIBRARIES Qt::PrintSupport)
    endif()''',
    "omit desktop PrintSupport on Android",
)

edit(
    "muse_deps/buildtools/manifest.cmake",
    r'''    if (_extdeps_sys STREQUAL "Windows")
        set(LIB_OS "windows")
    elseif (_extdeps_sys MATCHES "Darwin|macOS")
        set(LIB_OS "macos")
    else()
        set(LIB_OS "linux")
    endif()''',
    r'''    if (_extdeps_sys STREQUAL "Android")
        set(LIB_OS "android")
    elseif (_extdeps_sys STREQUAL "Windows")
        set(LIB_OS "windows")
    elseif (_extdeps_sys MATCHES "Darwin|macOS")
        set(LIB_OS "macos")
    else()
        set(LIB_OS "linux")
    endif()''',
    "resolve external dependencies for Android instead of host Linux",
)

edit(
    "muse_deps/buildtools/manifest.cmake",
    r'''if (NOT DEFINED LIB_ARCH OR LIB_ARCH STREQUAL "")
    if (LIB_OS STREQUAL "macos")''',
    r'''if (NOT DEFINED LIB_ARCH OR LIB_ARCH STREQUAL "")
    if (LIB_OS STREQUAL "android")
        if (CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
            set(LIB_ARCH "aarch64")
        else()
            message(FATAL_ERROR "Unsupported Android dependency ABI: ${CMAKE_ANDROID_ARCH_ABI}")
        endif()
    elseif (LIB_OS STREQUAL "macos")''',
    "map Android ABI to dependency architecture",
)

edit(
    "SetupConfigure.cmake",
    r'''set(QT_SUPPORT ON)

if (NOT MUSE_MODULE_UI)''',
    r'''set(QT_SUPPORT ON)

# Keep Audacity's original Qt application and audio engine. Disable only
# desktop integrations that have no Android implementation in this port yet.
if(OS_IS_ANDROID)
    set(QT_QPROCESS_SUPPORTED OFF)
    set(MUSE_MODULE_DIAGNOSTICS_CRASHPAD_CLIENT OFF)
    set(MUSE_MODULE_UPDATE OFF)
    set(AU_USE_PORTMIXER OFF)
endif()

if (NOT MUSE_MODULE_UI)''',
    "disable desktop-only integrations for Android",
)

edit(
    "src/app/CMakeLists.txt",
    r'''###########################################
# Wasm
###########################################
elseif(OS_IS_WASM)''',
    r'''###########################################
# Android
###########################################
elseif(OS_IS_ANDROID)
    # Qt's Android deployment step packages the executable and Qt runtime
    # into the APK. Android has no desktop install layout.

###########################################
# Wasm
###########################################
elseif(OS_IS_WASM)''',
    "allow Qt Android APK deployment",
)

print("Android source overlay applied.")
