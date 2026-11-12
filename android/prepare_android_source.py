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
    "src/appshell/qml/Audacity/AppShell/CMakeLists.txt",
    r'''elseif(OS_IS_LIN OR OS_IS_FREEBSD)
    qt_target_qml_sources(appshell_qml
        QML_FILES
            platform/linux/Main.qml
    )
else()
    message(FATAL_ERROR "Unsupported OS")
endif()''',
    r'''elseif(OS_IS_LIN OR OS_IS_FREEBSD OR OS_IS_ANDROID)
    # Audacity 4.0.2 has no Android-specific AppShell QML entry point yet.
    # Use the generic Linux shell as the closest existing non-native-menu
    # implementation so Android can configure without pretending to be Linux.
    qt_target_qml_sources(appshell_qml
        QML_FILES
            platform/linux/Main.qml
    )
else()
    message(FATAL_ERROR "Unsupported OS")
endif()''',
    "select existing generic AppShell QML entry point for Android",
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
    r'''    -DwxUSE_SECRETSTORE=OFF
)''',
    r'''    -DwxUSE_SECRETSTORE=OFF
    -DwxUSE_INTL=ON
)''',
    "enable wxWidgets internationalization in its base CMake configuration",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")

    set(_bd_generator''',
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")

    # Audacity's wxLocale-based language manager requires wxUSE_INTL.
    # Force this at the final nested configure boundary, rather than relying
    # on a platform override whose BD_OS may differ across manifest versions.
    if(BD_NAME STREQUAL "wxwidgets" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        list(APPEND _dep_cmake_args -DwxUSE_INTL=ON -DwxUSE_GUI=OFF)
        message(STATUS "[wxwidgets] forcing wxUSE_INTL=ON for Android")
    endif()

    set(_bd_generator''',
    "force wxWidgets locale support in the actual nested CMake configure",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    _bd_run(${CMAKE_COMMAND} ${_configure_args})
    _bd_run(${CMAKE_COMMAND} --build "${BUILD}" --config ${BD_CONFIG} --target install --parallel)''',
    r'''    _bd_run(${CMAKE_COMMAND} ${_configure_args})

    # Verify the actual generated wx/setup.h, not the Android platform header.
    # This catches a silently ignored or overridden wxUSE_INTL cache option
    # before spending time compiling wxWidgets and Audacity.
    if(BD_NAME STREQUAL "wxwidgets" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        file(STRINGS "${BUILD}/CMakeCache.txt" _wx_intl_cache REGEX "^wxUSE_INTL:BOOL=")
        if(NOT _wx_intl_cache STREQUAL "wxUSE_INTL:BOOL=ON")
            message(FATAL_ERROR "[wxwidgets] nested CMake did not retain wxUSE_INTL=ON: ${_wx_intl_cache}")
        endif()

        file(GLOB_RECURSE _wx_setup_headers "${BUILD}/*/wx/setup.h")
        set(_wx_intl_setup_found FALSE)
        foreach(_wx_setup_header IN LISTS _wx_setup_headers)
            file(READ "${_wx_setup_header}" _wx_setup_text)
            if(_wx_setup_text MATCHES "#define wxUSE_INTL 1")
                set(_wx_intl_setup_found TRUE)
            endif()
        endforeach()
        if(NOT _wx_intl_setup_found)
            message(FATAL_ERROR "[wxwidgets] CMake cache says wxUSE_INTL=ON but generated wx/setup.h does not")
        endif()
        message(STATUS "[wxwidgets] verified wxUSE_INTL=1 in generated wx/setup.h")
    endif()

    _bd_run(${CMAKE_COMMAND} --build "${BUILD}" --config ${BD_CONFIG} --target install --parallel)''',
    "verify wxWidgets internationalization in its generated setup header",
)

edit(
    "au3/libraries/au3-strings/Internat.cpp",
    r'''#elif defined(__WXMSW__)
    wxPathFormat format = wxPATH_WIN;
#endif''',
    r'''#elif defined(__WXMSW__)
    wxPathFormat format = wxPATH_WIN;
#elif defined(__ANDROID__)
    // Android uses POSIX path rules for filenames.
    wxPathFormat format = wxPATH_UNIX;
#endif''',
    "select POSIX filename rules for Android in Audacity string utilities",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    if(os STREQUAL "windows" OR os STREQUAL "macos")
        return()
    endif()''',
    r'''    # Android shared libraries must keep their platform-native loader
    # metadata. Do not run the Linux patchelf/RPATH rewrite on Android.
    if(os STREQUAL "windows" OR os STREQUAL "macos" OR os STREQUAL "android")
        return()
    endif()''',
    "skip desktop ELF RPATH rewriting for Android dependencies",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    # Apply patches
    foreach(_patch ${DEP_PATCHES})''',
    r'''    # wxWidgets bundles zlib. Its gz*.c files use POSIX file APIs
    # (read/write/close/lseek/unlink) without consistently including
    # unistd.h. Add the declaration header to each affected source file.
    # Patch only the extracted wxWidgets copy, leaving upstream archives intact.
    if(BD_NAME STREQUAL "wxwidgets" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        file(GLOB _wx_zlib_posix_sources "${SRC}/src/zlib/gz*.c")
        if(NOT _wx_zlib_posix_sources)
            message(FATAL_ERROR "[wxwidgets] bundled zlib gz*.c sources were not found")
        endif()
        foreach(_wx_zlib_source ${_wx_zlib_posix_sources})
            file(READ "${_wx_zlib_source}" _wx_zlib_text)
            if(NOT _wx_zlib_text MATCHES "#include <unistd.h>")
                string(PREPEND _wx_zlib_text "#include <unistd.h>\\n")
                file(WRITE "${_wx_zlib_source}" "${_wx_zlib_text}")
            endif()
        endforeach()
        message(STATUS "[wxwidgets] added Android POSIX declarations to bundled zlib sources")
        
        # wxWidgets 3.2's unsigned literal [0u] is ambiguous with its
        # int/long/size_t wxString overloads under Android NDK Clang.
        # Use the int overload explicitly; this is the same first character.
        set(_wx_filename_header "${SRC}/include/wx/filename.h")
        if(NOT EXISTS "${_wx_filename_header}")
            message(FATAL_ERROR "[wxwidgets] wx/filename.h was not found")
        endif()
        file(READ "${_wx_filename_header}" _wx_filename_text)
        if(_wx_filename_text MATCHES "GetPathSeparators\\(format\\)\\[0u\\]")
            string(REPLACE
                [=[GetPathSeparators(format)[0u]]=]
                [=[GetPathSeparators(format)[0]]=]
                _wx_filename_text "${_wx_filename_text}")
            file(WRITE "${_wx_filename_header}" "${_wx_filename_text}")
            message(STATUS "[wxwidgets] fixed ambiguous wxString index for Android Clang")
        elseif(NOT _wx_filename_text MATCHES "GetPathSeparators\\(format\\)\\[0\\]")
            message(FATAL_ERROR "[wxwidgets] unexpected wx/filename.h path separator expression")
        endif()

        # wxWidgets 3.2.6 ships an Android config header written for 32-bit
        # ARM. This build targets arm64-v8a: correct the ABI size macros and
        # let wxString expose its unsigned-int subscript overload. Without
        # this, wxSIZE_T_IS_UINT suppresses that overload and Clang reports
        # ambiguous operator[] calls throughout wxBase.
        set(_wx_android_config "${SRC}/include/wx/android/config_android.h")
        if(NOT EXISTS "${_wx_android_config}")
            message(FATAL_ERROR "[wxwidgets] Android config header was not found")
        endif()
        file(READ "${_wx_android_config}" _wx_android_config_text)
        string(REPLACE
            [=[#define SIZEOF_LONG 4]=]
            [=[#define SIZEOF_LONG 8]=]
            _wx_android_config_text "${_wx_android_config_text}")
        string(REPLACE
            [=[#define SIZEOF_SIZE_T 4]=]
            [=[#define SIZEOF_SIZE_T 8]=]
            _wx_android_config_text "${_wx_android_config_text}")
        string(REPLACE
            [=[#define SIZEOF_VOID_P 4]=]
            [=[#define SIZEOF_VOID_P 8]=]
            _wx_android_config_text "${_wx_android_config_text}")
        string(REPLACE
            [=[#define wxSIZE_T_IS_UINT 1]=]
            [=[/* wxSIZE_T_IS_UINT is false for arm64-v8a. */]=]
            _wx_android_config_text "${_wx_android_config_text}")

        # wxWidgets 3.2.6's Android config header does not define wxUSE_INTL.
        # Its generated wx/setup.h comes from build/cmake/setup.h.in instead.
        # Keep internationalization controlled by the real wxWidgets CMake
        # option passed to the nested configure, not by this platform header.

        if(_wx_android_config_text MATCHES "#define SIZEOF_LONG 4"
           OR _wx_android_config_text MATCHES "#define SIZEOF_SIZE_T 4"
           OR _wx_android_config_text MATCHES "#define SIZEOF_VOID_P 4"
           OR _wx_android_config_text MATCHES "#define wxSIZE_T_IS_UINT 1")
            message(FATAL_ERROR "[wxwidgets] failed to correct 32-bit Android ABI macros for arm64")
        endif()
        file(WRITE "${_wx_android_config}" "${_wx_android_config_text}")
        message(STATUS "[wxwidgets] corrected Android config sizes for arm64-v8a")

        # wxWidgets 3.2.6's datetime.cpp calls wxUILocale unconditionally,
        # but wxUILocale is declared only when wxUSE_INTL=1. Android's
        # wxBase configuration disables intl, so keep the English fallback
        # and compile the locale-specific call only when intl is enabled.
        set(_wx_datetime_source "${SRC}/src/common/datetime.cpp")
        if(NOT EXISTS "${_wx_datetime_source}")
            message(FATAL_ERROR "[wxwidgets] src/common/datetime.cpp was not found")
        endif()
        file(READ "${_wx_datetime_source}" _wx_datetime_text)
        string(REPLACE
            [=[wxString name = wxUILocale::GetCurrent().GetMonthName(month, flags);]=]
            [=[wxString name;
#if wxUSE_INTL
    name = wxUILocale::GetCurrent().GetMonthName(month, flags);
#endif]=]
            _wx_datetime_text "${_wx_datetime_text}")
        string(REPLACE
            [=[wxString name = wxUILocale::GetCurrent().GetWeekDayName(wday, flags);]=]
            [=[wxString name;
#if wxUSE_INTL
    name = wxUILocale::GetCurrent().GetWeekDayName(wday, flags);
#endif]=]
            _wx_datetime_text "${_wx_datetime_text}")
        if(_wx_datetime_text MATCHES "wxString name = wxUILocale::GetCurrent")
            message(FATAL_ERROR "[wxwidgets] failed to guard wxUILocale calls for wxUSE_INTL")
        endif()
        file(WRITE "${_wx_datetime_source}" "${_wx_datetime_text}")
        message(STATUS "[wxwidgets] guarded wxUILocale calls when wxUSE_INTL is disabled")
    endif()

    # Apply patches
    foreach(_patch ${DEP_PATCHES})''',
    "add Android unistd declaration to wxWidgets bundled zlib",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    # Apply patches
    foreach(_patch ${DEP_PATCHES})''',
    r'''    # Android bionic provides pthread symbols through libc and has no
    # separate libpthread.so. Remove PortAudio's desktop-only link dependency.
    if(BD_NAME STREQUAL "portaudio" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        set(_portaudio_cmake "${SRC}/CMakeLists.txt")
        if(NOT EXISTS "${_portaudio_cmake}")
            message(FATAL_ERROR "PortAudio CMakeLists.txt was not found")
        endif()
        file(READ "${_portaudio_cmake}" _portaudio_text)
        string(REPLACE
            [=[SET(PA_LIBRARY_DEPENDENCIES ${PA_LIBRARY_DEPENDENCIES} m pthread)]=]
            [=[SET(PA_LIBRARY_DEPENDENCIES ${PA_LIBRARY_DEPENDENCIES} m)]=]
            _portaudio_text "${_portaudio_text}")
        if(_portaudio_text MATCHES "PA_LIBRARY_DEPENDENCIES[^\\n]*pthread")
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
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")''',
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")

    # HarfBuzz's optional FreeType bridge is not needed for Audacity's
    # Android text shaping path. Disable only this optional integration.
    if(BD_NAME STREQUAL "harfbuzz" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        string(REPLACE
            [=[-DHB_HAVE_FREETYPE=ON]=]
            [=[-DHB_HAVE_FREETYPE=OFF]=]
            _dep_cmake_args "${_dep_cmake_args}")
        if(_dep_cmake_args MATCHES "HB_HAVE_FREETYPE=ON")
            message(FATAL_ERROR "[harfbuzz] failed to disable optional FreeType bridge")
        endif()
        message(STATUS "[harfbuzz] disabled optional FreeType bridge for Android")
    endif()''',
    "disable optional HarfBuzz FreeType bridge for Android",
)

edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")''',
    r'''    string(REPLACE "@RECIPE_DIR@" "${BD_RECIPE_DIR}" _dep_cmake_args "${DEP_CMAKE_ARGS}")

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


edit(
    "muse_deps/buildtools/build_dependency.cmake",
    r'''    _bd_run(${CMAKE_COMMAND} --build "${BUILD}" --config ${BD_CONFIG} --target install --parallel)''',
    r'''    _bd_run(${CMAKE_COMMAND} --build "${BUILD}" --config ${BD_CONFIG} --target install --parallel)

    # The generated setup.h is correct in wxWidgets' build tree, but the
    # dependency install step can leave a different setup.h in the prefix.
    # Audacity consumes the installed prefix, so synchronize that exact file.
    if(BD_NAME STREQUAL "wxwidgets" AND CMAKE_SYSTEM_NAME STREQUAL "Android")
        set(_wx_generated_setup "${BUILD}/lib/wx/include/base-unicode-3.2/wx/setup.h")
        set(_wx_installed_setup "${CMAKE_BINARY_DIR}/_deps/wxwidgets/lib/wx/include/base-unicode-3.2/wx/setup.h")
        if(NOT EXISTS "${_wx_generated_setup}")
            message(FATAL_ERROR "[wxwidgets] generated base-unicode setup.h is missing: ${_wx_generated_setup}")
        endif()
        file(READ "${_wx_generated_setup}" _wx_generated_setup_text)
        if(NOT _wx_generated_setup_text MATCHES "#define wxUSE_INTL 1")
            message(FATAL_ERROR "[wxwidgets] generated build-tree setup.h does not enable wxUSE_INTL")
        endif()
        get_filename_component(_wx_installed_setup_dir "${_wx_installed_setup}" DIRECTORY)
        file(MAKE_DIRECTORY "${_wx_installed_setup_dir}")
        configure_file("${_wx_generated_setup}" "${_wx_installed_setup}" COPYONLY)
        file(READ "${_wx_installed_setup}" _wx_installed_setup_text)
        if(NOT _wx_installed_setup_text MATCHES "#define wxUSE_INTL 1")
            message(FATAL_ERROR "[wxwidgets] installed setup.h still does not enable wxUSE_INTL")
        endif()
        message(STATUS "[wxwidgets] synchronized installed base-unicode setup.h with wxUSE_INTL=1")
    endif()''',
    "synchronize the exact installed wxWidgets setup.h consumed by Audacity",
)

print("Android source overlay applied.")
