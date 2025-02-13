import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import openvr
import argparse
import math
from helpers import extract_position, extract_orientation

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Visualize LED positions and hit line.")
parser.add_argument("--use-offset", action="store_true", help="Apply the calibration offset to the hit line.")
args = parser.parse_args()

# Load LED positions
def load_led_positions():
    try:
        with open("led_mapping.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("No LED mapping found.")
        return {}

# Load rotation offsets from calibration data
def load_calibration_offsets():
    """Load yaw, pitch, and roll offsets from calibration_data.json."""
    try:
        with open("calibration_data.json", "r") as f:
            data = json.load(f)
            return (
                data.get("offset_yaw", 0),  # Default to 0 if missing
                data.get("offset_pitch", 0),
                data.get("offset_roll", 0)
            )
    except (FileNotFoundError, KeyError):
        return 0, 0, 0  # Default to no rotation offset

# ✅ Load offsets at the start
offset_yaw, offset_pitch, offset_roll = load_calibration_offsets()


# Get current VR controller position & direction
def get_controller_pose(vr_system, device_index):
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )
    pose = poses[device_index]

    if pose.bDeviceIsConnected and pose.bPoseIsValid:
        position = extract_position(pose.mDeviceToAbsoluteTracking)
        direction = extract_orientation(pose.mDeviceToAbsoluteTracking)
        return np.array(position), np.array(direction)
    
    return None, None

# Apply rotation offset to direction
def apply_rotation_offset(direction, offset_yaw, offset_pitch):
    """
    Apply yaw and pitch offsets to the aiming direction.

    Args:
        direction (np.array): The original direction vector.
        offset_yaw (float): Yaw rotation offset (radians).
        offset_pitch (float): Pitch rotation offset (radians).

    Returns:
        np.array: Adjusted direction with yaw and pitch corrections.
    """
    # Extract current yaw and pitch
    original_yaw = math.atan2(direction[2], direction[0])
    original_pitch = math.asin(direction[1])  # Up/down angle

    # Apply yaw offset
    adjusted_yaw = original_yaw - offset_yaw  # 🔥 Reverse sign if needed
    adjusted_pitch = original_pitch - offset_pitch  # 🔥 Reverse sign if needed

    # Convert back to direction vector
    adjusted_direction = np.array([
        math.cos(adjusted_pitch) * math.cos(adjusted_yaw),  # X component
        math.sin(adjusted_pitch),  # Y component (vertical aim)
        math.cos(adjusted_pitch) * math.sin(adjusted_yaw)   # Z component
    ])

    return adjusted_direction


# Visualization Setup
fig, ax = plt.subplots()
led_positions = load_led_positions()


# Convert LED positions to 2D (XZ plane)
led_x = [led_positions[key][0] for key in led_positions]
led_z = [led_positions[key][2] for key in led_positions]
led_scatter = ax.scatter(led_x, led_z, c='blue', label="LEDs")

# Initialize hit line(s)
hit_line, = ax.plot([], [], 'r-', lw=2, label="Hit Line (Default)")
hit_line_offset, = ax.plot([], [], 'g--', lw=2, label="Hit Line (With Offset)" if args.use_offset else "")

ax.invert_yaxis()  

# OpenVR Initialization
openvr.init(openvr.VRApplication_Scene)
vr_system = openvr.VRSystem()

def update(frame):
    """Update function for animation"""
    global offset_yaw, offset_pitch  # ✅ Ensure these variables exist

    # Get controller position & direction
    position, direction = get_controller_pose(vr_system, 1)  # Assuming controller index 1
    if position is None or direction is None:
        return hit_line, hit_line_offset

    # Define hit line endpoint (Default)
    line_length = 2  
    end_x = position[0] + direction[0] * line_length
    end_z = position[2] + direction[2] * line_length

    # Update default hit line
    hit_line.set_data([position[0], end_x], [position[2], end_z])

    # Apply calibration rotation if enabled
    if args.use_offset:
        adjusted_direction = apply_rotation_offset(direction, offset_yaw, offset_pitch)

        # Define hit line endpoint (Offset)
        end_x_offset = position[0] + adjusted_direction[0] * line_length
        end_z_offset = position[2] + adjusted_direction[2] * line_length

        # Update hit line (Offset)
        hit_line_offset.set_data([position[0], end_x_offset], [position[2], end_z_offset])
    
    return hit_line, hit_line_offset


# Animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=False)

# Plot settings
ax.set_xlabel("X Axis")
ax.set_ylabel("Z Axis")
ax.set_title("LED Positions & Hit Line Visualization")

# Dynamically adjust legend based on offset usage
legend_labels = ["LEDs", "Hit Line (Default)"]
if args.use_offset:
    legend_labels.append("Hit Line (With Offset)")

ax.legend(legend_labels)
ax.grid(True)

# Show visualization
plt.show()

# Cleanup
openvr.shutdown()
