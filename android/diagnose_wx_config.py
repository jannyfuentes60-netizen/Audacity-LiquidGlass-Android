#!/usr/bin/env python3
"""Inspect wxUSE_CONFIG in the exact Audacity translation unit that failed."""
import json
import re
import shlex
import subprocess
from pathlib import Path

database = Path("build/android-arm64/compile_commands.json")
if not database.is_file():
    raise SystemExit(f"Missing {database}; enable CMAKE_EXPORT_COMPILE_COMMANDS")

entries = json.loads(database.read_text(encoding="utf-8"))
matches = [
    item for item in entries
    if item.get("file", "").endswith("EffectAutomationParameters.cpp")
]
if not matches:
    candidates = [item.get("file", "") for item in entries
                  if "EffectAutomationParameters" in item.get("file", "")]
    raise SystemExit(
        "The failing EffectAutomationParameters.cpp translation unit is absent "
        f"from compile_commands.json. Related entries: {candidates}"
    )

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
    return subprocess.run(
        clean + extra,
        cwd=entry["directory"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

macros = run(["-E", "-dM"])
if macros.returncode:
    print(macros.stderr[-12000:])
    raise SystemExit("Preprocessor macro inspection failed for the exact TU")

config = re.search(r"^#define wxUSE_CONFIG (\d+)$", macros.stdout, re.M)
intl = re.search(r"^#define wxUSE_INTL (\d+)$", macros.stdout, re.M)
print(f"Translation unit: {entry['file']}")
print(f"wxUSE_CONFIG: {config.group(1) if config else 'UNDEFINED'}")
print(f"wxUSE_INTL: {intl.group(1) if intl else 'UNDEFINED'}")

preprocessed = run(["-E"])
if preprocessed.returncode:
    print(preprocessed.stderr[-12000:])
    raise SystemExit("Full preprocessing failed for the exact TU")

has_declaration = bool(re.search(
    r"\bclass\s+(?:[A-Za-z_][A-Za-z0-9_]*\s+)*wxFileConfig\b",
    preprocessed.stdout,
))
print(f"wxFileConfig declaration visible: {'YES' if has_declaration else 'NO'}")

trace = run(["-E", "-H", "-o", "/dev/null"])
headers = [
    line.strip() for line in trace.stderr.splitlines()
    if "wx/setup.h" in line or "wx/fileconf.h" in line
]
print("Resolved wx headers:")
for line in headers:
    print(f"  {line}")

if not config or config.group(1) != "1" or not has_declaration:
    raise SystemExit(
        "wxWidgets configuration is not visible to the exact Audacity TU; "
        "stop before compiling Audacity."
    )
print("wxFileConfig is visible to the exact Audacity TU.")
