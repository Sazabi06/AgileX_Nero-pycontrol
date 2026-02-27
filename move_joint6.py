#!/usr/bin/env python3
"""
move_joint6.py
Rotate joint 6 of the robot by +10 degrees using pyAgxArm
Fully debugged and robust against CAN/connect delays.
"""

import time
import math
from pyAgxArm import create_agx_arm_config, AgxArmFactory

# -------------------------------
# Helper function: degrees -> radians
# -------------------------------
def deg2rad(deg):
    return deg * math.pi / 180

# -------------------------------
# Configuration
# -------------------------------
ROBOT_NAME = "nero"       # Robot model name
CAN_CHANNEL = "can0"      # CAN interface name
ROTATE_DEG = 10           # Rotation amount in degrees
JOINT_INDEX = 5           # Joint 6 (0-based index)
TIMEOUT = 10.0            # Max wait for joint feedback (seconds)

# -------------------------------
# Step 1: Create robot configuration
# -------------------------------
print("[DEBUG] Creating robot configuration...")
cfg = create_agx_arm_config(robot=ROBOT_NAME, comm="can", channel=CAN_CHANNEL)

# -------------------------------
# Step 2: Create robot instance
# -------------------------------
print("[DEBUG] Creating robot instance...")
robot = AgxArmFactory.create_arm(cfg)

# -------------------------------
# Step 3: Connect to robot
# -------------------------------
print("[DEBUG] Connecting to robot...")
try:
    robot.connect()
except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")
    exit(1)

# Short delay to allow initial CAN messages
time.sleep(0.5)

# -------------------------------
# Step 4: Wait for valid joint feedback
# -------------------------------
print("[DEBUG] Waiting for valid joint feedback...")
start_time = time.time()
ja = robot.get_joint_angles()
counter = 0
while ja is None:
    counter += 1
    if time.time() - start_time > TIMEOUT:
        raise RuntimeError("[ERROR] Timeout: no joint feedback received from robot. Check CAN bus and power.")
    if counter % 10 == 0:  # print message every 10 loops (~0.5s)
        print("[DEBUG] Still waiting for joint feedback...")
    ja = robot.get_joint_angles()
    time.sleep(0.05)  # small delay to reduce CPU usage

current_joints = ja.msg
print(f"[DEBUG] Current joint positions (radians): {current_joints}")

# -------------------------------
# Step 5: Compute target joint positions
# -------------------------------
rotation_radians = deg2rad(ROTATE_DEG)
target_joints = current_joints.copy()
target_joints[JOINT_INDEX] += rotation_radians
print(f"[DEBUG] Target joint positions (radians): {target_joints}")

# -------------------------------
# Step 6: Command robot to move
# -------------------------------
print(f"[DEBUG] Sending command to rotate joint {JOINT_INDEX+1} by {ROTATE_DEG} degrees...")
robot.command_joint_positions(target_joints)

# Short delay to allow robot to move
time.sleep(0.2)

# -------------------------------
# Step 7: Verify new joint positions
# -------------------------------
ja_new = robot.get_joint_angles()
if ja_new is not None:
    new_joints = ja_new.msg
    delta_deg = math.degrees(new_joints[JOINT_INDEX] - current_joints[JOINT_INDEX])
    print(f"[DEBUG] New joint positions (radians): {new_joints}")
    print(f"[DEBUG] Joint {JOINT_INDEX+1} moved by {delta_deg:.2f} degrees")
else:
    print("[WARNING] Could not read updated joint angles. Robot may not have sent feedback yet.")

print("[DEBUG] Done.")

