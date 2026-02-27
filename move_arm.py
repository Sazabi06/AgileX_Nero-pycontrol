#!/usr/bin/env python3
"""
Move Nero arm joints — uses DEGREES for convenience.

Modes:
  1) All joints:     python3 move_arm.py 0 25 -25 0 -25 0 0
  2) Named preset:   python3 move_arm.py home
  3) Single joint:   python3 move_arm.py j2 30       (move J2 to 30°)
  4) Relative move:  python3 move_arm.py +10 0 0 0 0 0 0   (nudge J1 by +10°)
  5) Show position:  python3 move_arm.py pos

Presets:
  home   → all joints to 0°
  rest   → relaxed pose: [0, 30, -30, 0, -30, 0, 0]°
  up     → arm straight up: [0, 90, 0, 0, 0, 0, 0]°

Joint limits (degrees):
  J1: [-155, 155]   J2: [-100, 100]   J3: [-158, 158]
  J4: [ -58, 123]   J5: [-158, 158]   J6: [ -42,  55]
  J7: [ -90,  90]

Options:
  --speed N   Set speed percent (1-100, default: 100)
  --rad       Interpret angles as radians instead of degrees
"""

import math
import sys
import time
from pyAgxArm import create_agx_arm_config, AgxArmFactory

# ── Joint limits (radians) ──────────────────────────────────────────
JOINT_LIMITS_RAD = [
    (-2.705261, 2.705261),
    (-1.745330, 1.745330),
    (-2.757621, 2.757621),
    (-1.012291, 2.146755),
    (-2.757621, 2.757621),
    (-0.733039, 0.959932),
    (-1.570797, 1.570797),
]

# ── Presets (degrees) ───────────────────────────────────────────────
PRESETS = {
    "home":  [0,  0,   0,  0,   0, 0, 0],
    "rest":  [0, 30, -30,  0, -30, 0, 0],
    "up":    [0, 90,   0,  0,   0, 0, 0],
}


def deg2rad(d):
    return d * math.pi / 180.0


def rad2deg(r):
    return r * 180.0 / math.pi


def fmt_deg(radians):
    """Format a list of radian values as degrees for display."""
    return "[" + ", ".join(f"{rad2deg(r):6.1f}°" for r in radians) + "]"


def validate_limits(joints_rad):
    """Check joint values against limits. Returns list of warnings."""
    warnings = []
    for i, (val, (lo, hi)) in enumerate(zip(joints_rad, JOINT_LIMITS_RAD)):
        if val < lo - 0.01 or val > hi + 0.01:
            warnings.append(
                f"  J{i+1}: {rad2deg(val):.1f}° outside [{rad2deg(lo):.0f}°, {rad2deg(hi):.0f}°]"
            )
    return warnings


def connect_and_enable():
    """Connect to arm and enable joints. Returns (robot, current_pos_rad)."""
    cfg = create_agx_arm_config(
        robot="nero", comm="can", channel="can0", interface="socketcan"
    )
    robot = AgxArmFactory.create_arm(cfg)
    robot.connect()

    print("Enabling joints...")
    start_t = time.monotonic()
    while not robot.enable():
        if time.monotonic() - start_t > 10.0:
            print("ERROR: enable timeout (10s)")
            sys.exit(1)
        time.sleep(0.01)

    ja = robot.get_joint_angles()
    current = list(ja.msg) if ja else [0.0] * 7
    return robot, current


def move_and_monitor(robot, joints_rad, speed=100):
    """Send move_j and monitor until done or timeout."""
    robot.set_speed_percent(speed)
    print(f"Moving to: {fmt_deg(joints_rad)}")
    robot.move_j(joints_rad)

    time.sleep(0.5)
    start_t = time.monotonic()
    while True:
        ja_now = robot.get_joint_angles()
        status = robot.get_arm_status()
        elapsed = time.monotonic() - start_t
        if ja_now and status:
            print(f"  [{elapsed:.1f}s] {fmt_deg(ja_now.msg)}  {status.msg.motion_status}")
        if status is not None and status.msg.motion_status == 0:
            print("Arm reached target position!")
            break
        if elapsed > 10.0:
            print("Motion monitoring timeout (10s).")
            break
        time.sleep(0.5)

    ja_final = robot.get_joint_angles()
    if ja_final:
        print(f"Final: {fmt_deg(ja_final.msg)}")


def parse_args():
    """Parse CLI args. Returns (target_rad, speed) or exits."""
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # Extract --speed N
    speed = 100
    if "--speed" in args:
        idx = args.index("--speed")
        speed = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    # Extract --rad flag
    use_rad = "--rad" in args
    if use_rad:
        args.remove("--rad")

    # ── "pos" command ──
    if args[0].lower() == "pos":
        return "pos", speed

    # ── Named preset ──
    if args[0].lower() in PRESETS:
        degs = PRESETS[args[0].lower()]
        return [deg2rad(d) for d in degs], speed

    # ── Single joint: j2 30 ──
    if len(args) == 2 and args[0].lower().startswith("j"):
        try:
            joint_idx = int(args[0][1:]) - 1
            if not 0 <= joint_idx < 7:
                raise ValueError
        except ValueError:
            print(f"Invalid joint name: {args[0]}  (use j1..j7)")
            sys.exit(1)
        val = float(args[1])
        if not use_rad:
            val = deg2rad(val)
        return ("single", joint_idx, val), speed

    # ── All 7 joints ──
    if len(args) != 7:
        print(f"Expected 7 joint values, got {len(args)}. See usage:\n")
        print(__doc__)
        sys.exit(1)

    raw = [float(a.lstrip("+")) if not a.startswith("+") and not a.startswith("-")
           else float(a) for a in args]
    is_relative = any(a.startswith("+") for a in args)

    if use_rad:
        values = raw
    else:
        values = [deg2rad(v) for v in raw]

    if is_relative:
        return ("relative", values), speed
    return values, speed


def main():
    result, speed = parse_args()

    # ── Show current position ──
    if result == "pos":
        cfg = create_agx_arm_config(
            robot="nero", comm="can", channel="can0", interface="socketcan"
        )
        robot = AgxArmFactory.create_arm(cfg)
        robot.connect()
        time.sleep(0.5)
        ja = robot.get_joint_angles()
        if ja:
            rads = list(ja.msg)
            print(f"Degrees: {fmt_deg(rads)}")
            print(f"Radians: [{', '.join(f'{r:.4f}' for r in rads)}]")
        else:
            print("No joint feedback")
        return

    robot, current = connect_and_enable()
    print(f"Current: {fmt_deg(current)}")

    # ── Compute target ──
    if isinstance(result, tuple) and result[0] == "single":
        _, joint_idx, val = result
        target = list(current)
        target[joint_idx] = val
        print(f"Moving J{joint_idx+1} to {rad2deg(val):.1f}°")

    elif isinstance(result, tuple) and result[0] == "relative":
        _, deltas = result
        target = [c + d for c, d in zip(current, deltas)]
        changed = [i for i, d in enumerate(deltas) if abs(d) > 1e-6]
        parts = [f"J{i+1} {'+' if deltas[i]>=0 else ''}{rad2deg(deltas[i]):.1f}°" for i in changed]
        print(f"Relative: {', '.join(parts) if parts else 'no change'}")

    else:
        target = result

    # ── Validate limits ──
    warnings = validate_limits(target)
    if warnings:
        print("WARNING — joints out of range:")
        for w in warnings:
            print(w)
        print("Continuing anyway...")

    move_and_monitor(robot, target, speed)
    print("Done.")


if __name__ == "__main__":
    main()
