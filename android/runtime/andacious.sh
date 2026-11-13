#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(realpath "$0")"
sudo rm -f "$SCRIPT_PATH" || true

# Expose Android shared folders inside the Debian userspace.
for folder in sdcard Documents Downloads Music Pictures Videos DCIM; do
  if [ -d "/$folder" ] && [ ! -e "$HOME/$folder" ]; then
    ln -s "/$folder" "$HOME/$folder"
  fi
done

xterm &

if [ ! -f /support/gdk_fix ]; then
  update-mime-database /usr/share/mime
  find /usr/lib -name gdk-pixbuf-query-loaders -exec {} --update-cache \; 2>/dev/null || true
  touch /support/gdk_fix
fi

if [ ! -f /support/full_screen_fix ]; then
  sed -i 's#</applications>#<application title="Audacity 4.0.2"><position force="yes"><x>0</x><y>0</y></position><size><width>100%</width><height>100%</height></size></application></applications>#g' /etc/xdg/openbox/rc.xml
  openbox --reconfigure || true
  touch /support/full_screen_fix
fi

APP_HOME="$HOME/.local/share/audacity-4.0.2"
APPIMAGE="$APP_HOME/audacity-linux-4.0.2-aarch64.AppImage"
APP_DIR="$APP_HOME/squashfs-root"
APPIMAGE_URL="https://github.com/audacity/audacity/releases/download/Audacity-4.0.2/audacity-linux-4.0.2-aarch64.AppImage"
EXPECTED_SHA256="88b1e16dd40a5b7d36bec5789b03f66bda34a7b964e19f338951bf6034d9db9c"

mkdir -p "$APP_HOME"

if [ ! -s "$APPIMAGE" ]; then
  echo "Downloading official Audacity 4.0.2 ARM64..."
  curl -fL --retry 3 --retry-delay 2 "$APPIMAGE_URL" -o "$APPIMAGE"
  printf '%s  %s\n' "$EXPECTED_SHA256" "$APPIMAGE" | sha256sum -c -
  chmod 755 "$APPIMAGE"
fi

if [ ! -x "$APP_DIR/AppRun" ]; then
  echo "Extracting Audacity 4.0.2 (FUSE is not required)..."
  TMP_DIR="$(mktemp -d "$APP_HOME/extract.XXXXXX")"
  trap 'rm -rf "$TMP_DIR"' EXIT
  (cd "$TMP_DIR" && "$APPIMAGE" --appimage-extract >/dev/null)
  if [ ! -x "$TMP_DIR/squashfs-root/AppRun" ]; then
    echo "ERROR: AppImage extraction did not produce AppRun."
    exit 1
  fi
  rm -rf "$APP_DIR"
  mv "$TMP_DIR/squashfs-root" "$APP_DIR"
  rm -rf "$TMP_DIR"
  trap - EXIT
fi

# Remove the Debian-provided Audacity package so the old editor is not left
# installed alongside the 4.0.2 AppImage.
if dpkg-query -W -f='${Status}' audacity 2>/dev/null | grep -q 'install ok installed'; then
  echo "Removing the older Debian Audacity package..."
  sudo apt-get purge -y audacity audacity-data
fi

echo "Launching the original Audacity 4.0.2 application..."
exec "$APP_DIR/AppRun" "$@"
