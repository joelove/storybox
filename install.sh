#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root (use sudo)."
    exit 1
fi

echo "=== Storybox Installation ==="

echo ""
echo "[1/5] Enabling SPI interface..."
raspi-config nonint do_spi 0

echo "[2/5] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3-venv python3-dev alsa-utils

echo "[3/5] Creating Python virtual environment..."
python3 -m venv --system-site-packages "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install --quiet --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "[4/5] Setting up audio directory and mappings..."
mkdir -p "$SCRIPT_DIR/audio"
if [ ! -f "$SCRIPT_DIR/mappings.json" ]; then
    echo "{}" > "$SCRIPT_DIR/mappings.json"
fi

echo "[5/5] Installing systemd service..."
cp "$SCRIPT_DIR/storybox.service" /etc/systemd/system/storybox.service
systemctl daemon-reload
systemctl enable storybox.service

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Reboot to activate SPI: sudo reboot"
echo "  2. Add WAV files to: $SCRIPT_DIR/audio/"
echo "  3. Register cards: sudo $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/src/register.py"
echo "  4. The service will start automatically on boot."
echo "     Manual start: sudo systemctl start storybox"
