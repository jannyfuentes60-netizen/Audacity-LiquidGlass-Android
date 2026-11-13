#!/usr/bin/env python3
"""Prepare the Andacious Android shell to launch the official Audacity 4.0.2 ARM64 AppImage.

The original Andacious repository points at a UserLAndLibrary submodule that is
not currently publicly fetchable at its pinned URL. This build uses a pinned
public historical mirror and applies the small package/API changes required
to build the Andacious wrapper against it.
"""
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

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


def ensure_android_namespaces():
    """Add AGP 8 namespaces to older Android modules using their manifest package."""
    for gradle_file in ANDACIOUS.rglob("build.gradle"):
        content = gradle_file.read_text(encoding="utf-8")
        if not re.search(r"com\.android\.(application|library)", content):
            continue
        if re.search(r"\bnamespace\s+", content):
            continue

        manifest = gradle_file.parent / "src/main/AndroidManifest.xml"
        package = None
        if manifest.is_file():
            match = re.search(r"""package=["']([^"']+)["']""", manifest.read_text(encoding="utf-8"))
            if match:
                package = match.group(1)

        if not package:
            app_id = re.search(r"""applicationId\s+["']([^"']+)["']""", content)
            if app_id:
                package = app_id.group(1)

        if not package:
            for source_root in (gradle_file.parent / "src/main/java", gradle_file.parent / "src/main/kotlin"):
                if not source_root.is_dir():
                    continue
                for source in source_root.rglob("*"):
                    if source.suffix not in (".java", ".kt"):
                        continue
                    match = re.search(r"^package\s+([A-Za-z0-9_.]+)", source.read_text(encoding="utf-8", errors="ignore"), re.M)
                    if match:
                        package = match.group(1)
                        break
                if package:
                    break

        if not package:
            raise RuntimeError(f"Cannot infer Android namespace for {gradle_file}")

        if not re.search(r"android\s*\{", content):
            raise RuntimeError(f"Android block not found in {gradle_file}")
        content = re.sub(
            r"(android\s*\{)",
            lambda match: match.group(1) + "\n    namespace '" + package + "'",
            content,
            count=1,
        )
        gradle_file.write_text(content, encoding="utf-8")
        print(f"Added namespace {package} to {gradle_file}", flush=True)


def patch_gradle_report_api():
    """Migrate removed Gradle 8 report properties across every included module."""
    patched = 0
    for gradle_file in ANDACIOUS.rglob("*.gradle"):
        content = gradle_file.read_text(encoding="utf-8")
        updated = re.sub(r"\b(xml|html|csv)\.enabled\s*=", r"\1.required =", content)
        updated = re.sub(r"\b(xml|html|csv)\.destination\b", r"\1.outputLocation", updated)
        if updated != content:
            gradle_file.write_text(updated, encoding="utf-8")
            patched += 1
            print(f"Migrated Gradle report API in {gradle_file}", flush=True)

    # Fail during preparation, with a useful path, rather than at Gradle
    # configuration time if another module still uses removed report APIs.
    remaining = []
    for gradle_file in ANDACIOUS.rglob("*.gradle"):
        content = gradle_file.read_text(encoding="utf-8")
        if re.search(r"\b(?:xml|html|csv)\.enabled\s*=", content):
            remaining.append(str(gradle_file))
        if re.search(r"\b(?:xml|html|csv)\.destination\b", content):
            remaining.append(str(gradle_file))
    if remaining:
        raise RuntimeError("Unmigrated Gradle report API in: " + ", ".join(sorted(set(remaining))))
    print(f"Gradle 8 report API audit passed; migrated {patched} build file(s).", flush=True)



def patch_android_build_config():
    """Enable BuildConfig only in Android modules that declare custom fields."""
    patched = []
    for gradle_file in ANDACIOUS.rglob("build.gradle"):
        content = gradle_file.read_text(encoding="utf-8")
        if not re.search(r"\bbuildConfigField\b", content):
            continue
        if not re.search(r"com\.android\.(application|library)", content):
            continue
        if re.search(r"buildFeatures\s*\{[^}]*\bbuildConfig\s+true", content, re.S):
            continue
        if not re.search(r"android\s*\{", content):
            raise RuntimeError(f"Android block missing in module with BuildConfig fields: {gradle_file}")
        updated = re.sub(
            r"(android\s*\{)",
            lambda match: match.group(1) + "\n    buildFeatures { buildConfig true }",
            content,
            count=1,
        )
        gradle_file.write_text(updated, encoding="utf-8")
        patched.append(str(gradle_file))

    # Verify every Android module declaring custom BuildConfig fields has the
    # feature explicitly enabled; don't defer this known AGP 8 failure to Gradle.
    unresolved = []
    for gradle_file in ANDACIOUS.rglob("build.gradle"):
        content = gradle_file.read_text(encoding="utf-8")
        if re.search(r"\bbuildConfigField\b", content) and re.search(
            r"com\.android\.(application|library)", content
        ) and not re.search(
            r"buildFeatures\s*\{[^}]*\bbuildConfig\s+true", content, re.S
        ):
            unresolved.append(str(gradle_file))
    if unresolved:
        raise RuntimeError("BuildConfig feature not enabled in: " + ", ".join(unresolved))
    print(
        "Android BuildConfig audit passed; enabled in "
        + str(len(patched))
        + " module(s): "
        + (", ".join(patched) if patched else "no changes needed"),
        flush=True,
    )


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
        LIBRARY / "termux-app" / "terminal-emulator" / "build.gradle",
        LIBRARY / "remote-desktop-clients" / "bVNC",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("UserLAndLibrary mirror is missing required paths:\n" + "\n".join(missing))

    ensure_android_namespaces()
    patch_gradle_report_api()
    patch_android_build_config()

    # Replace the removed Kotlin Android Extensions synthetic view accessors
    # with typed findViewById properties. This keeps the existing layouts and
    # behavior intact without depending on the removed compiler plugin.
    android_ns = "{http://schemas.android.com/apk/res/android}"
    view_types = {
        "Toolbar": "androidx.appcompat.widget.Toolbar",
        "ConstraintLayout": "androidx.constraintlayout.widget.ConstraintLayout",
        "BottomNavigationView": "com.google.android.material.bottomnavigation.BottomNavigationView",
        "TextInputEditText": "com.google.android.material.textfield.TextInputEditText",
        "FloatingActionButton": "com.google.android.material.floatingactionbutton.FloatingActionButton",
        "SwipeRefreshLayout": "androidx.swiperefreshlayout.widget.SwipeRefreshLayout",
        "RecyclerView": "androidx.recyclerview.widget.RecyclerView",
    }
    android_widgets = {
        "TextView", "EditText", "Button", "ImageButton", "ImageView", "CheckBox",
        "RadioButton", "RadioGroup", "Spinner", "ListView", "GridView", "LinearLayout",
        "RelativeLayout", "FrameLayout", "ScrollView", "HorizontalScrollView",
        "ToggleButton", "ProgressBar", "Switch", "SeekBar", "ViewFlipper",
    }

    def resolve_view_type(element):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "view":
            tag = element.attrib.get("class", "android.view.View")
        if tag == "fragment":
            return "android.view.View"
        if "." in tag:
            return tag
        if tag in view_types:
            return view_types[tag]
        if tag in android_widgets:
            return "android.widget." + tag
        if tag in ("View", "ViewStub"):
            return "android.view." + tag
        return "android.view.View"

    migrated_synthetics = 0
    for source in (LIBRARY / "app" / "src" / "main").rglob("*.kt"):
        source_text = source.read_text(encoding="utf-8", errors="ignore")
        imports = re.findall(
            r"(?m)^import kotlinx\.android\.synthetic\.main\.([A-Za-z0-9_]+)\.\*[^\n]*\n?",
            source_text,
        )
        if not imports:
            continue

        id_types = {}
        for layout_name in imports:
            layout_file = LIBRARY / "app" / "src" / "main" / "res" / "layout" / (layout_name + ".xml")
            if not layout_file.is_file():
                raise RuntimeError(f"Synthetic import references missing layout: {layout_file}")
            try:
                root = ET.parse(layout_file).getroot()
            except ET.ParseError as error:
                raise RuntimeError(f"Cannot parse synthetic layout {layout_file}: {error}") from error
            for element in root.iter():
                resource_id = element.attrib.get(android_ns + "id", "")
                match = re.fullmatch(r"@\+id/([A-Za-z0-9_]+)", resource_id)
                if not match:
                    continue
                view_id = match.group(1)
                view_type = resolve_view_type(element)
                if view_id in id_types and id_types[view_id] != view_type:
                    raise RuntimeError(
                        f"Conflicting synthetic view types for {view_id} in {source}: "
                        f"{id_types[view_id]} vs {view_type}"
                    )
                id_types[view_id] = view_type

        source_without_imports = re.sub(
            r"(?m)^import kotlinx\.android\.synthetic\.main\.[^\n]+\n?",
            "",
            source_text,
        )
        used = []
        for view_id, view_type in id_types.items():
            if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(view_id) + r"(?![A-Za-z0-9_])", source_without_imports):
                used.append((view_id, view_type))
        if not used:
            source.write_text(source_without_imports, encoding="utf-8")
            migrated_synthetics += 1
            continue

        class_name = source.stem
        class_match = re.search(
            r"(?m)^class\s+" + re.escape(class_name) + r"\b[^\n{]*\{\s*",
            source_without_imports,
        )
        if not class_match:
            raise RuntimeError(f"Cannot locate class declaration for synthetic migration: {source}")
        is_activity = class_name == "MainActivity"
        root_expression = "findViewById" if is_activity else "requireView().findViewById"
        getters = "\n" + "\n".join(
            f"    private val {view_id}: {view_type} get() = {root_expression}(R.id.{view_id})"
            for view_id, view_type in used
        ) + "\n\n"
        migrated = (
            source_without_imports[:class_match.end()]
            + getters
            + source_without_imports[class_match.end():]
        )
        source.write_text(migrated, encoding="utf-8")
        print(
            f"Migrated {len(used)} synthetic view accessor(s) in {source.relative_to(LIBRARY)}",
            flush=True,
        )
        migrated_synthetics += 1

    # The Parcelize compiler plugin was also bundled in Android Extensions.
    # Move its import to the supported standalone plugin if this source uses it.
    parcelize_used = False
    for source in (LIBRARY / "app" / "src" / "main").rglob("*.kt"):
        source_text = source.read_text(encoding="utf-8", errors="ignore")
        if "kotlinx.android.parcel.Parcelize" in source_text:
            source.write_text(
                source_text.replace(
                    "kotlinx.android.parcel.Parcelize",
                    "kotlinx.parcelize.Parcelize",
                ),
                encoding="utf-8",
            )
            parcelize_used = True
    if parcelize_used:
        parcelize_gradle = LIBRARY / "app" / "build.gradle"
        parcelize_content = parcelize_gradle.read_text(encoding="utf-8")
        if "kotlin-parcelize" not in parcelize_content:
            parcelize_content += "\napply plugin: 'kotlin-parcelize'\n"
            parcelize_gradle.write_text(parcelize_content, encoding="utf-8")

    # Verify that no removed Android Extensions imports remain.
    remaining_synthetics = []
    for source in (LIBRARY / "app" / "src" / "main").rglob("*.kt"):
        if "kotlinx.android.synthetic" in source.read_text(encoding="utf-8", errors="ignore"):
            remaining_synthetics.append(str(source))
    if remaining_synthetics:
        raise RuntimeError("Unmigrated Kotlin synthetic imports: " + ", ".join(remaining_synthetics))

    # Generate the FreeRDPCore Gradle project before dependency resolution.
    # Build only ARM64 and skip the unrelated Cerbero/GStreamer/SPICE stack.
    native_libs = LIBRARY / "remote-desktop-clients" / "remoteClientLib" / "jni" / "libs"
    deps_conf = native_libs / "build-deps.conf"
    deps_script = native_libs / "build-deps.sh"
    if not deps_conf.is_file() or not deps_script.is_file():
        raise SystemExit("The pinned remote-desktop-clients native dependency scripts are missing.")

    deps_content = deps_conf.read_text(encoding="utf-8")
    deps_content, changed = re.subn(r'(?m)^abis="[^"]*"', 'abis="arm64-v8a"', deps_content, count=1)
    if changed != 1:
        raise RuntimeError("Could not restrict native dependency ABI list to arm64-v8a.")
    deps_conf.write_text(deps_content, encoding="utf-8")

    deps_source = deps_script.read_text(encoding="utf-8")
    original = """# Parse command-line options
parallel=""
export ANDROID_NDK=$(install_ndk ./ ${ndk_version})
"""
    replacement = """# Parse command-line options
parallel=""
if [ "$1" = "freerdp-only" ]; then
    mkdir -p deps
    build_freerdp
    exit 0
fi
export ANDROID_NDK=$(install_ndk ./ ${ndk_version})
"""
    if original not in deps_source:
        raise RuntimeError("Could not add the isolated FreeRDP build mode to build-deps.sh.")
    deps_source = deps_source.replace(original, replacement, 1)

    old_config_patch = """               -e 's/WITH_JPEG=.*/WITH_JPEG=1/'\\
               -e 's/WITH_OPENH264=.*/WITH_OPENH264=1/'\\
               -e 's/OPENH264_TAG=.*/OPENH264_TAG=v2.1.1/'\\
               -e 's/NDK_TARGET=26/NDK_TARGET=21/'\\
"""
    new_config_patch = """               -e 's/WITH_JPEG=.*/WITH_JPEG=0/'\\
               -e 's/WITH_OPENH264=.*/WITH_OPENH264=0/'\\
               -e 's/BUILD_ARCH=.*/BUILD_ARCH="arm64-v8a"/'\\
               -e 's/NDK_TARGET=26/NDK_TARGET=21/'\\
"""
    if old_config_patch not in deps_source:
        raise RuntimeError("Could not apply the ARM64/minimal FreeRDP build configuration.")
    deps_source = deps_source.replace(old_config_patch, new_config_patch, 1)
    deps_source = deps_source.replace(
        "export OPENH264_NDK=$(install_ndk ../../ ${freerdp_openh264_ndk_version})",
        "export OPENH264_NDK=$ANDROID_NDK",
        1,
    )
    # OpenSSL 1.1.1's Android Configure script reads ANDROID_NDK_HOME,
    # while this legacy FreeRDP build only exports ANDROID_NDK. Keep both
    # variables aligned with the exact r21e toolchain selected by FreeRDP.
    ndk_export_pattern = r'(?m)^(\s*export ANDROID_NDK=\$\(install_ndk[^\n]*\))$'
    deps_source, ndk_exports_patched = re.subn(
        ndk_export_pattern,
        lambda match: match.group(1) + '\nexport ANDROID_NDK_HOME="$ANDROID_NDK"\nexport ANDROID_NDK_ROOT="$ANDROID_NDK"',
        deps_source,
        count=1,
    )
    if ndk_exports_patched != 1:
        raise RuntimeError("Could not align ANDROID_NDK_HOME with FreeRDP's pinned NDK.")
    deps_script.write_text(deps_source, encoding="utf-8")

    # Detect remaining Kotlin synthetic imports before the compiler does.
    synthetic_hits = []
    for source in (LIBRARY / "app" / "src").rglob("*.kt"):
        if "kotlinx.android.synthetic" in source.read_text(encoding="utf-8", errors="ignore"):
            synthetic_hits.append(str(source))
    if synthetic_hits:
        raise RuntimeError(
            "Kotlin synthetic view imports still require migration: " + ", ".join(synthetic_hits)
        )

    # These legacy Termux modules apply obsolete publishing plugins. They
    # are not needed to build the Android app and pull the unavailable Groovy
    # http-builder 0.7.2 artifact. Remove only those publishing declarations
    # from every affected module, retaining the Android library plugin.
    for module in ("terminal-emulator", "terminal-view"):
        terminal_gradle = LIBRARY / "termux-app" / module / "build.gradle"
        if not terminal_gradle.is_file():
            raise SystemExit(f"Required Termux Gradle file is missing: {terminal_gradle}")
        content = terminal_gradle.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?s)plugins\s*\{(?=[^}]*com\.jfrog\.bintray)(?=[^}]*com\.github\.dcendents\.android-maven)[^}]*\}\s*",
            "",
            content,
            count=1,
        )
        updated = re.sub(
            r"(?m)^apply from: ['\"]\.\./scripts/bintray-publish\.gradle['\"]\s*\n?",
            "",
            updated,
            count=1,
        )
        if "com.jfrog.bintray" in updated or "bintray-publish.gradle" in updated:
            raise RuntimeError(f"Legacy Bintray publishing plugin remains in {terminal_gradle}")
        if updated != content:
            terminal_gradle.write_text(updated, encoding="utf-8")
            print(f"Removed obsolete publishing plugins from {terminal_gradle}", flush=True)


    # Kotlin 2.x removed kotlin-android-extensions. Remove the obsolete plugin
    # and DSL block before Gradle configures the legacy UserLAnd app module.
    userland_gradle = LIBRARY / "app" / "build.gradle"
    userland_content = userland_gradle.read_text(encoding="utf-8")
    userland_content = re.sub(
        r"(?m)^\s*apply plugin: ['\"]kotlin-android-extensions['\"]\s*\n?",
        "",
        userland_content,
    )
    userland_content = re.sub(
        r"(?s)\nandroidExtensions\s*\{.*?\n\}\s*",
        "\n",
        userland_content,
        count=1,
    )
    userland_gradle.write_text(userland_content, encoding="utf-8")
    if "kotlin-android-extensions" in userland_content or re.search(r"(?m)^androidExtensions\s*\{", userland_content):
        raise RuntimeError("Obsolete Kotlin Android Extensions DSL remains in UserLAndLibrary/app/build.gradle")

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