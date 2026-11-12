#!/usr/bin/env python3
"""Expose the Qt 6.8.3 Android private header targets omitted by the binary kit.

KDDockWidgets' QtQuick backend uses QtGui private headers. The Android Qt kit
ships the versioned headers but does not ship the corresponding *Private
CMake package files, so create small interface-only packages that point at
the Android kit's own headers and public Android Qt targets. No host Qt
libraries or headers are mixed into the Android target.
"""
from pathlib import Path
import os
import sys

prefix = Path(os.environ["QT_ANDROID_ROOT"]).resolve()
version = os.environ.get("QT_VERSION", "6.8.3")
cmake_root = prefix / "lib" / "cmake"


def require(relative: str) -> Path:
    path = prefix / relative
    if not path.is_file():
        raise SystemExit(f"Missing required Android Qt private header: {path}")
    return path


def private_include_root(header: Path, module: str) -> Path:
    # Installed Qt private headers are laid out as:
    # include/<Module>/<version>/<Module>/private/<header>
    parts = header.parts
    needle = (module, version, module, "private")
    for i in range(len(parts) - len(needle) + 1):
        if tuple(parts[i:i + len(needle)]) == needle:
            return Path(*parts[:i + 2 + 1])  # include/<Module>/<version>
    raise SystemExit(
        f"Unexpected private-header layout for {header}; expected "
        f"include/{module}/{version}/{module}/private/..."
    )


gui_private = require(
    f"include/QtGui/{version}/QtGui/private/qhighdpiscaling_p.h"
)
gui_global_private = require(
    f"include/QtGui/{version}/QtGui/private/qtguiglobal_p.h"
)
gui_config_private = require(
    f"include/QtGui/{version}/QtGui/private/qtgui-config_p.h"
)
core_global_private = require(
    f"include/QtCore/{version}/QtCore/private/qglobal_p.h"
)

# KDDockWidgets includes this QPA header as <qpa/qplatformwindow.h>.
qpa_header = require("include/QtGui/qpa/qplatformwindow.h")

gui_versioned_root = private_include_root(gui_private, "QtGui")
core_versioned_root = private_include_root(core_global_private, "QtCore")
qpa_include_root = qpa_header.parent.parent

core_dir = cmake_root / "Qt6CorePrivate"
gui_dir = cmake_root / "Qt6GuiPrivate"
core_dir.mkdir(parents=True, exist_ok=True)
gui_dir.mkdir(parents=True, exist_ok=True)


def write_version_file(directory: Path) -> None:
    (directory / "Qt6PrivateConfigVersion.cmake").write_text(
        f'''set(PACKAGE_VERSION "{version}")
if(PACKAGE_FIND_VERSION)
  if(PACKAGE_FIND_VERSION VERSION_GREATER PACKAGE_VERSION)
    set(PACKAGE_VERSION_COMPATIBLE FALSE)
  else()
    set(PACKAGE_VERSION_COMPATIBLE TRUE)
    if(PACKAGE_FIND_VERSION VERSION_EQUAL PACKAGE_VERSION)
      set(PACKAGE_VERSION_EXACT TRUE)
    endif()
  endif()
endif()
''',
        encoding="utf-8",
    )
    # CMake expects the package-specific filename.
    package = "Qt6CorePrivate" if directory == core_dir else "Qt6GuiPrivate"
    (directory / f"{package}ConfigVersion.cmake").write_text(
        (directory / "Qt6PrivateConfigVersion.cmake").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (directory / "Qt6PrivateConfigVersion.cmake").unlink()


write_version_file(core_dir)
write_version_file(gui_dir)

(core_dir / "Qt6CorePrivateConfig.cmake").write_text(
    f'''include(CMakeFindDependencyMacro)
find_dependency(Qt6Core {version} CONFIG)
if(NOT TARGET Qt6::CorePrivate)
  add_library(Qt6::CorePrivate INTERFACE IMPORTED)
  set_target_properties(Qt6::CorePrivate PROPERTIES
    INTERFACE_LINK_LIBRARIES Qt6::Core
    INTERFACE_INCLUDE_DIRECTORIES "{core_versioned_root.as_posix()}"
  )
endif()
set(Qt6CorePrivate_FOUND TRUE)
set(Qt6CorePrivate_VERSION "{version}")
''',
    encoding="utf-8",
)

(gui_dir / "Qt6GuiPrivateConfig.cmake").write_text(
    f'''include(CMakeFindDependencyMacro)
find_dependency(Qt6Gui {version} CONFIG)
find_dependency(Qt6CorePrivate {version} CONFIG)
if(NOT TARGET Qt6::GuiPrivate)
  add_library(Qt6::GuiPrivate INTERFACE IMPORTED)
  set_target_properties(Qt6::GuiPrivate PROPERTIES
    INTERFACE_LINK_LIBRARIES "Qt6::Gui;Qt6::CorePrivate"
    INTERFACE_INCLUDE_DIRECTORIES "{gui_versioned_root.as_posix()};{core_versioned_root.as_posix()};{qpa_include_root.as_posix()}"
  )
endif()
set(Qt6GuiPrivate_FOUND TRUE)
set(Qt6GuiPrivate_VERSION "{version}")
''',
    encoding="utf-8",
)

print(f"Android Qt {version} private headers verified:")
print(f"  QtGui private: {gui_versioned_root}")
print(f"  QtCore private: {core_versioned_root}")
print(f"  QPA headers: {qpa_include_root}")
print("Generated Android-only Qt6CorePrivate and Qt6GuiPrivate CMake interface packages.")
