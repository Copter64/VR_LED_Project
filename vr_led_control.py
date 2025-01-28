import openvr
import numpy as np
import aiohttp
import asyncio
import json
import time
from collections import defaultdict
import socket

# WLED Configuration
WLED_IP = "192.168.1.186"  # Replace with your WLED IP
NUM_LEDS = 358  # Total number of LEDs on the strip

# SteamVR Settings
POINTER_ACCURACY = .9999  #Must be a float less than 1, the larger the number the more precise the virtual pointer is, the smaller lights more LEDs at a time

# Shared state for LED management
led_state = defaultdict(lambda: [0, 0, 0, 0])  # Tracks [R, G, B, fade_steps] for each LED

# File to save/load mapped LED positions
LED_MAPPING_FILE = "led_mapping.json"

# Debugging and Visualization Options
ENABLE_DEBUG = False
ENABLE_VISUALIZATION = False

# region: Helper Functions
def extract_position(matrix):
    """Extracts position (translation) from a 4x4 transformation matrix."""
    return matrix[0][3], matrix[1][3], matrix[2][3]

def extract_orientation(matrix):
    """Extracts orientation (rotation) as a forward vector from a 4x4 transformation matrix."""
    # Forward vector is the third column of the matrix
    forward_vector = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])
    return forward_vector

def is_trigger_pressed(vr_system, controller_index):
    """Checks if the trigger button is pressed on a specific controller."""
    success, controller_state = vr_system.getControllerState(controller_index)
    if not success:
        return False
    # Check if the trigger button is pressed
    trigger_mask = 1 << openvr.k_EButton_SteamVR_Trigger
    return controller_state.ulButtonPressed & trigger_mask != 0

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple to a HEX string.
    """
    return str('%02x%02x%02x' % rgb).upper()

def create_ddp_packet(pixel_data):
    """
    Create a DDP packet with the given pixel data.
    Args:
        pixel_data (bytes): RGB pixel data as bytes.
    Returns:
        bytes: A complete DDP packet.
    """
    # DDP header (10 bytes)
    header = bytearray(10)
    header[0] = 0x41  # Flags: Version 1, standard DDP
    header[1] = 0x00  # Reserved
    header[2:4] = (0).to_bytes(2, byteorder='big')  # Data offset
    header[4:8] = (0).to_bytes(4, byteorder='big')  # Application ID
    header[8:10] = len(pixel_data).to_bytes(2, byteorder='big')  # Data length

    return header + pixel_data

async def fps_loop_ddp(fps=60):
    """
    Continuously sends the current LED state to WLED as optimized DDP packets.
    Args:
        fps (int): Frames per second.
    """
    udp_ip = WLED_IP
    udp_port = 4048  # Default DDP port
    delay = 1 / fps

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Prepare pixel data (RGB values for all LEDs)
        pixel_data = bytearray()
        for i in range(NUM_LEDS):
            if i in led_state:
                r, g, b, _ = led_state[i]  # Extract RGB values
                pixel_data.extend([r, g, b])
            else:
                pixel_data.extend([0, 0, 0])  # Default to black/off

        # Create the DDP packet
        ddp_packet = create_ddp_packet(pixel_data)

        # Send the DDP packet via UDP
        sock.sendto(ddp_packet, (udp_ip, udp_port))

        # Wait for the next frame
        await asyncio.sleep(delay)


async def fade_leds(fade_delay=0.05):
    """
    Gradually dims LEDs in the shared state based on fade steps.
    Args:
        fade_delay (float): Time between fade steps (seconds).
    """
    while True:
        for led_index in list(led_state.keys()):
            color = led_state[led_index]
            if color[3] > 0:  # Check if fade steps remain
                fade_steps = color[3]
                led_state[led_index][:3] = [int(c * fade_steps / (fade_steps + 1)) for c in color[:3]]
                led_state[led_index][3] -= 1
            else:
                del led_state[led_index]  # Remove LED when fade is complete

        await asyncio.sleep(fade_delay)


def set_leds(led_index, color, fade_steps=None):
    """
    Activate or update a specific LED in the shared state.
    Args:
        led_index (int): Index of the LED to update.
        color (tuple): RGB color of the LED.
        fade_steps (int, optional): Number of fade steps. Defaults to None (no fading).
    """
    if fade_steps:
        led_state[led_index] = [*color, fade_steps]  # Add fade steps
    else:
        led_state[led_index] = [*color, 0]  # No fade steps
# endregion
        


def calculate_leds_to_light(controller_position, controller_direction, led_positions, calibration_data=None):
    """
    Calculate which LEDs to light up based on the controller's ray direction on a 2D plane (XZ).
    """
    lit_leds = []

    # Project controller position and direction onto the XZ plane
    controller_position_2d = np.array([controller_position[0], controller_position[2]])  # X, Z only
    controller_direction_2d = np.array([controller_direction[0], controller_direction[2]])  # X, Z only
    controller_direction_2d /= np.linalg.norm(controller_direction_2d)  # Normalize direction vector

    for led_index, led_position in led_positions.items():
        led_index = int(led_index)

        # Project LED position onto the XZ plane
        led_position_2d = np.array([led_position[0], led_position[2]])  # X, Z only

        # Calculate the vector from the controller to the LED in 2D
        to_led_2d = led_position_2d - controller_position_2d
        to_led_2d /= np.linalg.norm(to_led_2d)  # Normalize vector

        # Compare direction vectors
        dot_product = np.dot(controller_direction_2d, to_led_2d)
        if dot_product > POINTER_ACCURACY:  # Adjust threshold to control ray match sensitivity
            lit_leds.append(led_index)

    return lit_leds


def load_led_positions():
    """Load previously saved LED positions."""
    try:
        with open(LED_MAPPING_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("No saved LED mapping found. Run the mapping function first.")
        return {}

def visualize_line(position, direction):
    """Visualizes the line extending from the controller for debugging purposes."""
    print("Visualizing Line:")
    print(f"  Start Position: {position}")
    print(f"  Direction: {direction}")

# endregion


# region: LED Mapping
async def map_led_positions(vr_system):
    """Map the physical positions of LEDs using the controller."""
    mapped_positions = {}
    current_led = 0
    debounce_time = 0.5  # Time (in seconds) to wait before allowing the next trigger press
    last_trigger_time = 0  # Tracks the last time the trigger was pressed

    print("Starting LED mapping...")
    print("Point at each LED and pull the trigger to save its position. Press Ctrl+C to exit.")

    try:
        while current_led < NUM_LEDS:
            # Light up only the current LED
            print(f"Lighting up LED {current_led} for mapping...")
            await set_leds(current_led, (255, 255, 255))  # White color for mapping

            while True:
                poses = vr_system.getDeviceToAbsoluteTrackingPose(
                    openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
                )

                for device_index, pose in enumerate(poses):
                    if pose.bDeviceIsConnected and pose.bPoseIsValid:
                        device_class = vr_system.getTrackedDeviceClass(device_index)

                        if device_class == openvr.TrackedDeviceClass_Controller:
                            matrix = pose.mDeviceToAbsoluteTracking
                            position = extract_position(matrix)

                            print(f"LED {current_led}: Controller Position: {position}")

                            # Check if the trigger is pressed and debounce
                            if is_trigger_pressed(vr_system, device_index):
                                current_time = time.time()
                                if current_time - last_trigger_time > debounce_time:
                                    # Save position and move to next LED
                                    mapped_positions[current_led] = position
                                    print(f"Mapped LED {current_led} to position {position}")

                                    # Turn off the current LED
                                    await set_leds(current_led, (0, 0, 0))  # Turn off the current LED

                                    # Move to the next LED
                                    current_led += 1
                                    last_trigger_time = current_time  # Update debounce timer
                                    break

                if current_led >= NUM_LEDS:
                    break

    except KeyboardInterrupt:
        print("Mapping interrupted. Saving progress...")

    # Save mapping to a file
    with open(LED_MAPPING_FILE, 'w') as f:
        json.dump(mapped_positions, f, indent=4)
    print("LED mapping saved.")
    return mapped_positions
# endregion


# region: Main Program
async def main():
    """Main program to map LEDs and light them up based on controller position."""
    openvr.init(openvr.VRApplication_Scene)
    try:
        vr_system = openvr.VRSystem()
        print("Do you want to map LEDs or load an existing map? (map/load)")
        choice = input().strip().lower()

        if choice == "map":
            led_positions = await map_led_positions(vr_system)
        elif choice == "load":
            led_positions = load_led_positions()

            if not led_positions:
                print("No LED mapping data available. Exiting...")
                return
        else:
            print("Invalid choice. Exiting...")
            return

        print("Point your controller to light up LEDs. Press Ctrl+C to stop.")

        # Start FPS loop and fading logic
        asyncio.create_task(fps_loop_ddp(fps=30))
        asyncio.create_task(fade_leds(fade_delay=0.05))

        while True:
            poses = vr_system.getDeviceToAbsoluteTrackingPose(
                openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
            )

            for device_index, pose in enumerate(poses):
                if pose.bDeviceIsConnected and pose.bPoseIsValid:
                    device_class = vr_system.getTrackedDeviceClass(device_index)

                    if device_class == openvr.TrackedDeviceClass_Controller:
                        matrix = pose.mDeviceToAbsoluteTracking
                        position = extract_position(matrix)
                        direction = extract_orientation(matrix)

                        # Calculate which LEDs to light up
                        lit_leds = calculate_leds_to_light(position, direction, led_positions)

                        # Update shared state with new LEDs
                        for led in lit_leds:
                            set_leds(led, (255, 0, 0), fade_steps=20)  # Red color with fade

            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        openvr.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
# endregion