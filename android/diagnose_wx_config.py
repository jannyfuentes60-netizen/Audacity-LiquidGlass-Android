#!/usr/bin/env python3
"""Trace wxWidgets feature-macro origins in Audacity's exact translation unit."""
import json
import re
import shlex
import subprocess
from pathlib import Path

database = Path("build/android-arm64/compile_commands.json")
if not database.is_file():
    raise SystemExit(f"Missing {database}; enable CMAKE_EXPORT_COMPILE_COMMANDS")

entries = json.loads(database.read_text(encoding="utf-8"))
matches = [item for item in entries if item.get("file", "").endswith("EffectAutomationParameters.cpp")]
if not matches:
    raise SystemExit("EffectAutomationParameters.cpp is absent from compile_commands.json")

entry = matches[0]
args = entry.get("arguments") or shlex.split(entry["command"])
clean = []
skip_next = False
for arg in args:
    if skip_next:
        skip_next = False
        continue
    if arg in ("-o", "-MF", "-MT", "-MQ"):
        skip_next = True
        continue
    if arg in ("-c", "-MD", "-MMD", "-MP"):
        continue
    clean.append(arg)

def run(extra):
    return subprocess.run(clean + extra, cwd=entry["directory"], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

print(f"Translation unit: {entry['file']}")
print("wx-related compiler arguments:")
for i, arg in enumerate(clean):
    if (arg.startswith(("-Dwx", "-Uwx")) or
        (arg == "-include" and i + 1 < len(clean) and "wx" in clean[i + 1].lower())):
        print(f"  {arg}")
        if arg == "-include" and i + 1 < len(clean):
            print(f"  {clean[i + 1]}")

setup_path = (Path("build/android-arm64/_deps/wxwidgets/lib/wx/include/"
                   "base-unicode-3.2/wx/setup.h"))
if setup_path.is_file():
    setup_text = setup_path.read_text(encoding="utf-8", errors="replace")
    print(f"Installed setup.h: {setup_path.resolve()}")
    for macro in ("wxUSE_CONFIG", "wxUSE_INTL", "wxUSE_FILE",
                  "wxUSE_TEXTBUFFER", "wxUSE_TEXTFILE"):
        found = re.findall(rf"^\\s*#\\s*define\\s+{macro}\\s+.*$", setup_text, re.M)
        print(f"  setup.h {macro}: {found[-1].strip() if found else 'not defined'}")
else:
    print(f"Installed setup.h missing: {setup_path.resolve()}")

macros = run(["-E", "-dM"])
if macros.returncode:
    print(macros.stderr[-12000:])
    raise SystemExit("Preprocessor macro inspection failed")
for macro in ("wxUSE_CONFIG", "wxUSE_INTL", "wxUSE_FILE", "wxUSE_TEXTBUFFER", "wxUSE_TEXTFILE"):
    found = re.search(rf"^#define {macro} (\\d+)$", macros.stdout, re.M)
    print(f"Final {macro}: {found.group(1) if found else 'UNDEFINED'}")

history = run(["-E", "-dD"])
if history.returncode:
    print(history.stderr[-12000:])
    raise SystemExit("Preprocessor macro-history inspection failed")
print("Feature macro definition history (in preprocessing order):")
for line in history.stdout.splitlines():
    if re.match(r"^#\\s*(?:define|undef)\\s+wxUSE_(?:CONFIG|INTL|FILE|TEXTBUFFER|TEXTFILE)\\b", line):
        print(f"  {line}")

trace = run(["-E", "-H", "-o", "/dev/null"])
if trace.returncode:
    print(trace.stderr[-12000:])
    raise SystemExit("Header trace failed")
headers = [line.strip() for line in trace.stderr.splitlines()
           if "wx/setup.h" in line or "wx/fileconf.h" in line]
print("Resolved wx headers:")
for line in headers:
    print(f"  {line}")

preprocessed = run(["-E"])
if preprocessed.returncode:
    print(preprocessed.stderr[-12000:])
    raise SystemExit("Full preprocessing failed")
has_declaration = bool(re.search(
    r"\\bclass\\s+(?:[A-Za-z_][A-Za-z0-9_]*\\s+)*wxFileConfig\\b",
    preprocessed.stdout))
print(f"wxFileConfig declaration visible: {'YES' if has_declaration else 'NO'}")

if not has_declaration:
    raise SystemExit("wxFileConfig is not visible; see macro history and include trace above")
print("wxFileConfig declaration is visible to the exact Audacity TU.")
