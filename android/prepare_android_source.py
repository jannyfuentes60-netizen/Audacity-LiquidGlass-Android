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

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    if(CMAKE_CXX_COMPILER)
        list(APPEND _configure_args -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
    endif()    # Prepare initial cache variables''',
    r'''    if(CMAKE_CXX_COMPILER)
        list(APPEND _configure_args -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER})
    endif()

    # Nested dependency builds must use the same Android cross-compilation
    # toolchain as Audacity; forwarding compiler paths alone targets the host.
    foreach(_var
            CMAKE_TOOLCHAIN_FILE
            CMAKE_SYSTEM_NAME
            CMAKE_SYSTEM_VERSION
            CMAKE_ANDROID_NDK
            CMAKE_ANDROID_ARCH_ABI
            CMAKE_ANDROID_API
            CMAKE_ANDROID_STL_TYPE
            CMAKE_SYSROOT
            CMAKE_C_COMPILER_TARGET
            CMAKE_CXX_COMPILER_TARGET
            CMAKE_C_FLAGS
            CMAKE_CXX_FLAGS
            ANDROID_ABI
            ANDROID_PLATFORM
            ANDROID_NDK
            ANDROID_STL
            ANDROID_TOOLCHAIN)
        if(DEFINED ${_var} AND NOT "${${_var}}" STREQUAL "")
            list(APPEND _configure_args "-D${_var}=${${_var}}")
        endif()
    endforeach()

    # CMake's environment-based CFLAGS initialization is not guaranteed to
    # survive nested configure invocations. Explicitly preserve large-file
    # declarations required by FLAC on Android's bionic libc.
    if(ANDROID OR CMAKE_SYSTEM_NAME STREQUAL "Android")
        list(APPEND _configure_args
            "-DCMAKE_C_FLAGS=${CMAKE_C_FLAGS} -D_LARGEFILE_SOURCE=1"
            "-DCMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS} -D_LARGEFILE_SOURCE=1"
            "-DANDROID_ABI=arm64-v8a"
            "-DANDROID_PLATFORM=android-28")
    endif()

    # Prepare initial cache variables''',
    "forward Android toolchain into nested dependency builds",
)

edit(
    "muse_deps/recipes/wxwidgets/spec.cmake",
    r'''set(DEP_CMAKE_ARGS_LINUX   -DwxUSE_GUI=OFF)
set(DEP_CMAKE_ARGS_WINDOWS -DwxUSE_GUI=OFF)''',
    r'''set(DEP_CMAKE_ARGS_LINUX   -DwxUSE_GUI=OFF)
set(DEP_CMAKE_ARGS_WINDOWS -DwxUSE_GUI=OFF)
set(DEP_CMAKE_ARGS_ANDROID -DwxUSE_GUI=OFF)''',
    "build wxBase without a desktop GTK toolkit on Android",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    # Apply patches
    foreach(_patch ${DEP_PATCHES})''',
    r'''    # Android's bionic libc provides pthread symbols directly; unlike
    # desktop Linux it has no separate libpthread.so. PortAudio's upstream
    # CMakeLists unconditionally adds pthread to target link dependencies.
    if(BD_NAME STREQUAL "portaudio" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        set(_portaudio_cmake "${SRC}/CMakeLists.txt")
        if(NOT EXISTS "${_portaudio_cmake}")
            message(FATAL_ERROR "PortAudio CMakeLists.txt was not found")
        endif()
        file(READ "${_portaudio_cmake}" _portaudio_text)
        # Bracket arguments preserve the literal CMake variable in the
        # upstream source; normal quoted arguments expand it in this scope.
        string(REPLACE
            [=[SET(PA_LIBRARY_DEPENDENCIES ${PA_LIBRARY_DEPENDENCIES} m pthread)]=]
            [=[SET(PA_LIBRARY_DEPENDENCIES ${PA_LIBRARY_DEPENDENCIES} m)]=]
            _portaudio_text "${_portaudio_text}")
        if(_portaudio_text MATCHES "PA_LIBRARY_DEPENDENCIES[^\n]*pthread")
            message(FATAL_ERROR "Could not remove desktop libpthread dependency from PortAudio")
        endif()
        file(WRITE "${_portaudio_cmake}" "${_portaudio_text}")
        message(STATUS "[portaudio] removed separate libpthread dependency for Android")
    endif()

    # Apply patches
    foreach(_patch ${DEP_PATCHES})''',
    "remove unavailable separate pthread library from Android PortAudio link",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    '    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")',
    '''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")

    # Vorbis 1.3.7 uses FindOgg.cmake, which does not consume OggConfig.cmake
    # or the dependency prefix automatically. Pass the exact Ogg artifacts
    # from the already-built dependency prefix to its nested CMake configure.
    foreach(_dep_prefix ${BD_DEPENDS_PREFIXES})
        if(EXISTS "${_dep_prefix}/include/ogg/ogg.h"
           AND EXISTS "${_dep_prefix}/lib/libogg.so")
            list(APPEND _dep_cmake_args
                "-DOGG_LIBRARY=${_dep_prefix}/lib/libogg.so"
                "-DOGG_INCLUDE_DIR=${_dep_prefix}/include")
        endif()
    endforeach()''',
    "pass installed Ogg library and headers to Vorbis FindOgg",
)

print("Android source overlay applied.")
