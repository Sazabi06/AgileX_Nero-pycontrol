#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# install.sh — One-time setup for AgileX Nero on a fresh Ubuntu PC
#
# Usage:
#   bash install.sh
#
# What it does:
#   1. Installs system prerequisites (python3, pip, can-utils, etc.)
#   2. Creates a Python virtual environment (venv/)
#   3. Installs the pyAgxArm SDK and dependencies into the venv
#   4. Makes helper scripts executable
#
# After running this, activate the venv with:
#   source venv/bin/activate
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  AgileX Nero — Full Installation Script"
echo "============================================"
echo ""

# ── 1. System packages ──────────────────────────────────────────
echo "[1/4] Installing system packages ..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    can-utils ethtool net-tools \
    build-essential

echo "[OK] System packages installed."

# ── 2. Python virtual environment ───────────────────────────────
echo ""
echo "[2/4] Creating Python virtual environment ..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Created venv/"
else
    echo "  venv/ already exists — skipping"
fi

# Activate venv
source venv/bin/activate
echo "[OK] venv activated  ($(python3 --version))"

# ── 3. Install pyAgxArm SDK ─────────────────────────────────────
echo ""
echo "[3/4] Installing pyAgxArm and dependencies ..."
pip install --upgrade pip setuptools wheel -q
pip install -e . -q
echo "[OK] pyAgxArm installed."

# ── 4. Make scripts executable ───────────────────────────────────
echo ""
echo "[4/4] Making scripts executable ..."
chmod +x setup_can.sh rm_tmp.sh 2>/dev/null || true
echo "[OK] Done."

echo ""
echo "============================================"
echo "  Installation complete!"
echo ""
echo "  Next steps:"
echo "    1. source venv/bin/activate"
echo "    2. sudo bash setup_can.sh       # bring up CAN"
echo "    3. python3 move_arm.py home     # test arm"
echo "============================================"
