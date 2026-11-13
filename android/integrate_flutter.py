#!/usr/bin/env python3
"""Wire the Flutter Liquid Glass library module into the Andacious Android host.

The Flutter screen is the launcher/library only. Audacity continues to run in
Andacious' Linux session and is opened in its existing remote-desktop activity.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "android" / "andacious"
APP = HOST / "app"
MODULE_REPO = ROOT / "flutter_module" / "build" / "host" / "outputs" / "repo"
CHANNEL = "com.djfaraon.audacity/runtime"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def replace_once(path: Path, old: str, new: str):
    data = path.read_text(encoding="utf-8")
    if old not in data:
        raise RuntimeError(f"Expected integration point missing in {path}: {old!r}")
    path.write_text(data.replace(old, new, 1), encoding="utf-8")


def patch_gradle():
    root_gradle = HOST / "build.gradle"
    data = root_gradle.read_text(encoding="utf-8")
    marker = 'maven { url "https://jitpack.io" }'
    if marker not in data:
        raise RuntimeError("Could not find Andacious allprojects Maven repository block.")
    if "flutter_module/build/host/outputs/repo" not in data:
        data = data.replace(
            marker,
            marker + '\n            maven { url "$rootDir/../flutter_module/build/host/outputs/repo" }'
            + '\n            maven { url "https://storage.googleapis.com/download.flutter.io" }',
            1,
        )
        root_gradle.write_text(data, encoding="utf-8")

    app_gradle = APP / "build.gradle"
    data = app_gradle.read_text(encoding="utf-8")
    dependency = "implementation 'tech.ula.flutter_module:flutter_debug:1.0'"
    if dependency not in data:
        replace_once(
            app_gradle,
            "    implementation project(':UserLAndLibrary')",
            "    implementation project(':UserLAndLibrary')\n    " + dependency,
        )


def patch_manifest():
    manifest = APP / "src" / "main" / "AndroidManifest.xml"
    ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
    tree = ET.parse(manifest)
    root = tree.getroot()
    app = root.find("application")
    if app is None:
        raise RuntimeError("Andacious host manifest has no application element.")

    activity = None
    for candidate in app.findall("activity"):
        if candidate.get(ANDROID + "name") == "tech.ula.andacious.MainActivity":
            activity = candidate
            break
    if activity is None:
        raise RuntimeError("Could not find the Andacious launcher activity in its manifest.")

    normal_theme = "io.flutter.embedding.android.NormalTheme"
    if not any(item.get(ANDROID + "name") == normal_theme for item in activity.findall("meta-data")):
        ET.SubElement(activity, "meta-data", {
            ANDROID + "name": normal_theme,
            ANDROID + "resource": "@style/NormalTheme",
        })
    embedding = "flutterEmbedding"
    if not any(item.get(ANDROID + "name") == embedding for item in app.findall("meta-data")):
        ET.SubElement(app, "meta-data", {
            ANDROID + "name": embedding,
            ANDROID + "value": "2",
        })
    tree.write(manifest, encoding="utf-8", xml_declaration=True)

    values = APP / "src" / "main" / "res" / "values"
    values.mkdir(parents=True, exist_ok=True)
    styles = values / "styles_flutter.xml"
    styles.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<resources>\n'
        '    <style name="NormalTheme" parent="@android:style/Theme.Material.Light.NoActionBar">\n'
        '        <item name="android:windowBackground">?android:colorBackground</item>\n'
        '    </style>\n'
        '</resources>\n',
        encoding="utf-8",
    )


def write_flutter_host_activity():
    source = APP / "src" / "main" / "java" / "tech" / "ula" / "andacious" / "MainActivity.kt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        """package tech.ula.andacious

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import tech.ula.library.model.entities.App
import java.io.File

class MainActivity : FlutterActivity() {
    companion object {
        private const val CHANNEL = \"""" + CHANNEL + """\"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        saveIncomingUri(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        saveIncomingUri(intent)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    \"openAudacity\" -> {
                        try {
                            val launch = Intent(this, tech.ula.library.MainActivity::class.java)
                            launch.putExtra(
                                \"app\",
                                App(\"andacious\", \"sound\", \"debian\", false, true, \"false\", false, 1)
                            )
                            startActivity(launch)
                            result.success(null)
                        } catch (error: Exception) {
                            result.error(\"RUNTIME_START_FAILED\", error.message, null)
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun saveIncomingUri(source: Intent?) {
        val uri: Uri = source?.data ?: return
        val external = getExternalFilesDir(null) ?: return
        val intentDir = File(external, \"Intents\")
        if (!intentDir.exists() && !intentDir.mkdirs()) return
        val temporary = File(intentDir, \".url.txt\")
        val destination = File(intentDir, \"url.txt\")
        temporary.writeText(uri.toString())
        if (destination.exists()) destination.delete()
        temporary.renameTo(destination)
    }
}
""",
        encoding="utf-8",
    )


def main():
    if not (MODULE_REPO / "tech" / "ula" / "flutter_module" / "flutter_debug" / "1.0").exists():
        # Flutter's Maven repository layout is checked by Gradle itself; allow
        # the alternate artifact folder naming while still requiring a repo.
        if not MODULE_REPO.is_dir():
            raise SystemExit(
                "Flutter AAR repository is missing. Run flutter build aar --debug first."
            )
    if not (HOST / "settings.gradle").is_file() or not (APP / "build.gradle").is_file():
        raise SystemExit("Andacious Android host checkout is incomplete.")
    patch_gradle()
    patch_manifest()
    write_flutter_host_activity()
    print("Flutter library host integrated; Audacity remains in Andacious remote desktop.")


if __name__ == "__main__":
    main()
