#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# setup_can.sh — Bring up the CAN interface for AgileX Nero arm
#
# Usage:
#   sudo bash setup_can.sh              # defaults: can0, 1 Mbit/s
#   sudo bash setup_can.sh can0 1000000 # explicit name & bitrate
#
# Run this EVERY TIME after:
#   • Rebooting the PC
#   • Unplugging / re-plugging the USB-to-CAN adapter
#   • Opening a fresh terminal (if CAN was not yet activated)
#
# What it does:
#   1. Installs can-utils and ethtool if missing
#   2. Detects the CAN adapter on USB
#   3. Configures and brings up the interface
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

CAN_NAME="${1:-can0}"
BITRATE="${2:-1000000}"

echo "=== AgileX Nero — CAN Setup ==="
echo "Interface : $CAN_NAME"
echo "Bitrate   : $BITRATE"
echo ""

# ── 1. Ensure required packages ──────────────────────────────────
for pkg in can-utils ethtool net-tools; do
    if ! dpkg -s "$pkg" &>/dev/null; then
        echo "Installing $pkg ..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq "$pkg"
    fi
done
echo "[OK] System packages ready."

# ── 2. Detect CAN interface on USB ──────────────────────────────
IFACE=$(ip -br link show type can 2>/dev/null | awk '{print $1}' | head -1)

if [ -z "$IFACE" ]; then
    echo ""
    echo "ERROR: No CAN interface detected."
    echo "  • Is the USB-to-CAN adapter plugged in?"
    echo "  • Try: sudo modprobe gs_usb   (then re-run this script)"
    exit 1
fi

echo "[OK] Found CAN interface: $IFACE"

# ── 3. Rename interface if needed ────────────────────────────────
if [ "$IFACE" != "$CAN_NAME" ]; then
    echo "Renaming $IFACE → $CAN_NAME ..."
    sudo ip link set "$IFACE" down           2>/dev/null || true
    sudo ip link set "$IFACE" name "$CAN_NAME"
    IFACE="$CAN_NAME"
fi

# ── 4. Bring interface up ────────────────────────────────────────
sudo ip link set "$IFACE" down              2>/dev/null || true
sudo ip link set "$IFACE" type can bitrate "$BITRATE"
sudo ip link set "$IFACE" up

echo "[OK] $IFACE is UP at bitrate $BITRATE."
echo ""
echo "Quick verify:  candump $IFACE   (should show frames once arm is powered)"
echo "=== Done ==="
