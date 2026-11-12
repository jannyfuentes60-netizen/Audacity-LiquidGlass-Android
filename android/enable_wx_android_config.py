#!/usr/bin/env python3
"""Enable wxFileConfig in the Android wxWidgets build used by Audacity."""
from pathlib import Path

header = Path(
    "build/android-arm64/_deps/wxwidgets/include/wx/android/chkconf.h"
)
if not header.is_file():
    raise SystemExit(f"Missing wxWidgets Android configuration header: {header}")

text = header.read_text(encoding="utf-8")
disabled = "#undef wxUSE_CONFIG\n#define wxUSE_CONFIG 0\n"
marker = "// Audacity still compiles wx-based shared components; keep wxFileConfig enabled.\n"
if marker in text:
    print("wxUSE_CONFIG Android override is already applied.")
else:
    count = text.count(disabled)
    if count != 1:
        raise SystemExit(
            "Expected exactly one Android wxUSE_CONFIG disable block; "
            f"found {count}. Refusing to patch an unknown wxWidgets header."
        )
    text = text.replace(
        disabled,
        marker
        + "// Keep wxFileConfig enabled; its implementation is built in wxBase.\n",
        1,
    )
    header.write_text(text, encoding="utf-8")
    print(f"Enabled wxUSE_CONFIG in {header}")

if "#undef wxUSE_CONFIG\n#define wxUSE_CONFIG 0" in text:
    raise SystemExit("wxUSE_CONFIG is still forcibly disabled by chkconf.h")
