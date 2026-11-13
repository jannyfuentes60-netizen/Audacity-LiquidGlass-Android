#!/usr/bin/env python3
"""Prepare the Andacious Android shell to launch the official Audacity 4.0.2 ARM64 AppImage.

The original Andacious repository points at a UserLAndLibrary submodule that is
not currently publicly fetchable at its pinned URL. This build uses a pinned
public historical mirror and applies the small package/API changes required
to build the Andacious wrapper against it.
"""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ANDACIOUS = ROOT / "android" / "andacious"
LIBRARY = ANDACIOUS / "UserLAndLibrary"
LIBRARY_REPO = "https://github.com/foeget-ma/UserLAndLibrary.git"
LIBRARY_COMMIT = "9af1dcda5dcc6c5e62c331e8f06fbea20f63cc16"


def run(args, cwd=None):
    print("+", " ".join(str(x) for x in args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def replace_once(path: Path, old: str, new: str):
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise RuntimeError(f"Expected text not found in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def main():
    if not (ANDACIOUS / "settings.gradle").is_file():
        raise SystemExit(
            "Andacious submodule is missing. Run: git submodule update --init android/andacious"
        )

    # Replace the unavailable upstream submodule checkout with a pinned,
    # publicly fetchable mirror of the UserLAndLibrary source.
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)
    run(["git", "clone", LIBRARY_REPO, str(LIBRARY)])
    run(["git", "checkout", "--detach", LIBRARY_COMMIT], cwd=LIBRARY)
    run(["git", "submodule", "update", "--init", "--recursive"], cwd=LIBRARY)

    required = [
        LIBRARY / "app" / "src" / "main" / "java" / "tech" / "ula" / "MainActivity.kt",
        LIBRARY / "app" / "src" / "main" / "java" / "tech" / "ula" / "model" / "entities" / "App.kt",
        LIBRARY / "termux-app" / "app",
        LIBRARY / "remote-desktop-clients" / "bVNC",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("UserLAndLibrary mirror is missing required paths:\n" + "\n".join(missing))

    # Adapt Andacious' wrapper to the public mirror's package and App model.
    activity = ANDACIOUS / "app/src/main/java/tech/ula/andacious/MainActivity.kt"
    replace_once(
        activity,
        "import tech.ula.library.model.entities.App",
        "import tech.ula.model.entities.App",
    )
    replace_once(
        activity,
        "tech.ula.library.MainActivity::class.java",
        "tech.ula.MainActivity::class.java",
    )
    replace_once(
        activity,
        'App("andacious","sound", "debian", false, true, "false",false, 1)',
        'App("andacious", "sound", "debian", false, true, false, 1L)',
    )

    # Give the rebuilt wrapper its own app identity.
    replace_once(
        ANDACIOUS / "app/build.gradle",
        'applicationId "tech.ula.andacious"',
        'applicationId "com.djfaraon.audacity"',
    )
    replace_once(
        ANDACIOUS / "build.gradle",
        "appVersionName = '24.11.27'",
        "appVersionName = '4.0.2-android'",
    )
    replace_once(
        ANDACIOUS / "build.gradle",
        'provider_authority = "tech.ula.andacious.provider.fileprovider"',
        'provider_authority = "com.djfaraon.audacity.provider.fileprovider"',
    )
    replace_once(
        ANDACIOUS / "app/src/main/res/values/strings.xml",
        '<string name="app_name">Andacious</string>',
        '<string name="app_name">Audacity 4</string>',
    )

    launcher = ROOT / "android/runtime/andacious.sh"
    target_launcher = ANDACIOUS / "app/src/main/assets/apps/andacious/andacious.sh"
    shutil.copyfile(launcher, target_launcher)
    target_launcher.chmod(0o755)
    (ANDACIOUS / "app/src/main/assets/apps/andacious/andacious.txt").write_text(
        "Audacity 4.0.2 runs inside the Andacious Android/Linux compatibility layer.\n",
        encoding="utf-8",
    )

    print("Prepared Andacious to launch the official Audacity 4.0.2 AArch64 AppImage.")


if __name__ == "__main__":
    main()
