# AgileX Nero — Python Arm Controller

Control the **AgileX Nero 7-DOF robotic arm** from any Ubuntu PC over a USB-to-CAN adapter using the `pyAgxArm` SDK.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Hardware Setup](#hardware-setup)
3. [Quick Start (3 commands)](#quick-start-3-commands)
4. [Detailed Installation](#detailed-installation)
5. [CAN Bus Setup (required after every reboot)](#can-bus-setup)
6. [Using move_arm.py](#using-move_armpy)
7. [Using move_joint6.py](#using-move_joint6py)
8. [Python API Quick Reference](#python-api-quick-reference)
9. [Project Structure](#project-structure)
10. [Troubleshooting](#troubleshooting)
11. [Safety Notice](#safety-notice)
12. [License](#license)

---

## Requirements

| Category | Details |
|----------|---------|
| **OS** | Ubuntu 20.04 / 22.04 (recommended) / 24.04 |
| **Python** | 3.8 or higher |
| **Hardware** | AgileX Nero arm + 24 V power adapter + USB-to-CAN module |
| **USB port** | At least one USB-A port (or USB-C with adapter) |

---

## Hardware Setup

1. **Wire the CAN bus** — on the arm's aviation connector cable, strip the insulation to expose bare copper:
   - **Yellow** wire → CAN **H** terminal on the USB-to-CAN module
   - **Blue** wire → CAN **L** terminal on the USB-to-CAN module
   - Secure with a flathead screwdriver

2. **Plug the USB-to-CAN module** into a USB-A port on your PC

3. **Power the arm** — connect the 24 V adapter (100–240 V AC, 50/60 Hz) to the XT30 connector, then insert the aviation plug into the arm

4. **Wait for green LED** on the arm — this means initialization is complete

---

## Quick Start (3 commands)

```bash
# 1. Clone and install everything (one-time)
git clone [https://github.com/Sazabi06/AgileX_nero.git]
cd AgileX_nero
bash install.sh

# 2. Activate venv + bring up CAN (every reboot / new terminal)
source venv/bin/activate
sudo bash setup_can.sh

# 3. Move the arm!
python3 move_arm.py home
```

---

## Detailed Installation

### Step 1 — Clone the repo

```bash
git clone https://github.com/<YOUR_USERNAME>/AgileX_nero.git
cd AgileX_nero
```

### Step 2 — Run the installer

```bash
bash install.sh
```

This will:
- Install system packages: `python3`, `pip`, `python3-venv`, `can-utils`, `ethtool`, `net-tools`, `build-essential`
- Create a Python virtual environment in `venv/`
- Install `pyAgxArm` and its dependencies (`python-can`, `typing-extensions`)

### Step 3 — Activate the virtual environment

```bash
source venv/bin/activate
```

> **Every time you open a new terminal** you must reactivate:
> ```bash
> cd AgileX_nero
> source venv/bin/activate
> ```

---

## CAN Bus Setup

The CAN interface **does not persist across reboots**. You must run this after every reboot or USB reconnect:

```bash
sudo bash setup_can.sh
```

Default: interface `can0` at 1 Mbit/s. To customise:

```bash
sudo bash setup_can.sh can0 1000000     # explicit name and bitrate
```

### Verify CAN is working

```bash
candump can0
```

You should see a stream of CAN frames once the arm is powered on and CAN push is enabled (see [Enabling CAN Push](#enabling-can-push) below).

### Enabling CAN Push

**Option A — Via the Nero web interface:**
Connect to the arm's web UI and toggle "CAN Push" on.

**Option B — Via Python (programmatic):**
```python
from pyAgxArm import create_agx_arm_config, AgxArmFactory

cfg = create_agx_arm_config(robot="nero", comm="can", channel="can0", interface="socketcan")
robot = AgxArmFactory.create_arm(cfg)
robot.connect()
robot.set_normal_mode()   # switches to normal mode + enables CAN push
```

---

## Using move_arm.py

A full-featured CLI tool for moving the Nero arm. All angles are in **degrees** by default.

### Syntax

```
python3 move_arm.py [OPTIONS] <command>
```

### Commands

| Command | Example | Description |
|---------|---------|-------------|
| **Preset** | `python3 move_arm.py home` | Move to a named pose |
| **All joints** | `python3 move_arm.py 0 25 -25 0 -25 0 0` | Set all 7 joints (degrees) |
| **Single joint** | `python3 move_arm.py j2 30` | Move joint 2 to 30° |
| **Relative** | `python3 move_arm.py +10 0 0 0 0 0 0` | Nudge joint 1 by +10° |
| **Show position** | `python3 move_arm.py pos` | Print current joint angles |

### Presets

| Name | Angles (degrees) |
|------|-------------------|
| `home` | `[0, 0, 0, 0, 0, 0, 0]` |
| `rest` | `[0, 30, -30, 0, -30, 0, 0]` |
| `up` | `[0, 90, 0, 0, 0, 0, 0]` |

### Options

| Flag | Description |
|------|-------------|
| `--speed N` | Set speed percent, 1–100 (default: 100) |
| `--rad` | Interpret values as radians instead of degrees |

### Joint Limits

| Joint | Min (°) | Max (°) |
|-------|---------|---------|
| J1 | −155 | +155 |
| J2 | −100 | +100 |
| J3 | −158 | +158 |
| J4 | −58 | +123 |
| J5 | −158 | +158 |
| J6 | −42 | +55 |
| J7 | −90 | +90 |

### Examples

```bash
# Go to home position at 50% speed
python3 move_arm.py --speed 50 home

# Set all joints explicitly
python3 move_arm.py 0 25 -25 0 -25 0 0

# Move only joint 3 to -45°
python3 move_arm.py j3 -45

# Nudge joint 1 by +10° (relative to current)
python3 move_arm.py +10 0 0 0 0 0 0

# Show current position
python3 move_arm.py pos
```

---

## Using move_joint6.py

A simpler demo script that rotates **joint 6** by +10 degrees from its current position.

```bash
python3 move_joint6.py
```

---

## Python API Quick Reference

```python
from pyAgxArm import create_agx_arm_config, AgxArmFactory
import time

# Create config and connect
cfg = create_agx_arm_config(
    robot="nero", comm="can", channel="can0", interface="socketcan"
)
robot = AgxArmFactory.create_arm(cfg)
robot.connect()

# (Optional) Enable CAN push programmatically
robot.set_normal_mode()

# Enable all joints
while not robot.enable():
    time.sleep(0.01)

# Read joint angles
ja = robot.get_joint_angles()
print(ja.msg)              # list of 7 floats (radians)

# Move to a joint target (radians)
robot.set_speed_percent(80)
robot.move_j([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

# Read arm status
status = robot.get_arm_status()
print(status.msg.motion_status)  # 0 = idle, 1 = moving

# Disable / emergency stop
robot.disable()
robot.electronic_emergency_stop()
robot.reset()
```

---

## Project Structure

```
AgileX_nero/
├── install.sh              # One-time full setup (packages + venv + SDK)
├── setup_can.sh            # Bring up CAN interface (run after reboot)
├── move_arm.py             # Feature-rich CLI arm controller
├── move_joint6.py          # Simple single-joint demo
├── setup.py                # Python package setup
├── pyproject.toml          # PEP 517/518 build config
├── MANIFEST.in             # Package data manifest
├── LICENSE                 # LGPL v3
├── .gitignore              # Git ignore rules
├── rm_tmp.sh               # Clean build artifacts
├── README.md               # This file
│
├── pyAgxArm/               # SDK library
│   ├── __init__.py
│   ├── version.py
│   ├── api/                # Factory + config
│   ├── configs/            # Robot JSON configs (nero.json, piper.json)
│   ├── demos/              # Example scripts per robot model
│   │   └── nero/test1.py
│   ├── protocols/          # CAN protocol implementation
│   │   └── can_protocol/
│   │       ├── comms/      # CAN communication layer
│   │       ├── drivers/    # Per-robot drivers (nero, piper, ...)
│   │       └── msgs/       # CAN message definitions
│   ├── scripts/            # Shell scripts for CAN setup
│   │   ├── linux/
│   │   └── ubuntu/
│   ├── extensions/
│   └── utiles/             # Utility helpers (FPS, logging, transforms)
│
├── docs/                   # Documentation
│   ├── nero/
│   │   ├── First-TimeUserGuide(CAN).MD
│   │   └── nero-API使用文档.MD
│   ├── can_user.MD
│   ├── can_user(EN).MD
│   └── Q&A.MD
│
└── asserts/
    └── pictures/
        └── candump_can0.png
```

---

## Troubleshooting

### "No CAN interface detected"
- Is the USB-to-CAN adapter plugged in?
- Run `lsusb` to check if the adapter appears
- Try `sudo modprobe gs_usb` then re-run `sudo bash setup_can.sh`

### `candump can0` shows no data
- CAN push is not enabled — use the web UI or call `robot.set_normal_mode()` in Python
- The arm LED is not green — wait for initialization to complete
- H and L wires may be swapped
- Wire insulation not stripped — bare copper must touch the terminal

### `connect()` fails or hangs
- `can0` interface is not up — run `sudo bash setup_can.sh`
- Run `ip link show can0` to verify the interface state

### Python `ModuleNotFoundError: No module named 'pyAgxArm'`
- Virtual environment not activated — run `source venv/bin/activate`
- SDK not installed — run `pip install -e .`

### Permission error on CAN commands
- CAN setup requires root — use `sudo bash setup_can.sh`

### After reboot nothing works
After every reboot you must:
```bash
cd AgileX_nero
source venv/bin/activate      # re-activate Python venv
sudo bash setup_can.sh        # re-initialize CAN interface
```

---

## Safety Notice

- **Clear the workspace** — ensure no objects or people are within the arm's reach before sending motion commands
- **Do NOT send motion commands** when the arm is in an unknown state
- **Start with low speed** — use `--speed 30` until you are confident in the target pose
- **Emergency stop** — call `robot.electronic_emergency_stop()` or power off the adapter

---

## License

This project uses the `pyAgxArm` SDK by AgileX Robotics, licensed under **LGPL v3**.
See [LICENSE](LICENSE) for the full text.
