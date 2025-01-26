import asyncio
import openvr
import numpy as np
import aiohttp
import time
import json
import timeit

# WLED Configuration
WLED_IP = "192.168.1.186"  # Replace with your WLED IP
NUM_LEDS = 358  # Total number of LEDs on the strip

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

async def set_leds(current_led, color):
    """
    Light up a single LED on the WLED strip.
    Args:
        current_led (int): The index of the LED to light up.
        color (tuple): The RGB color of the LED (e.g., (255, 255, 255) for white).
    """
    api_endpoint = f"http://{WLED_IP}/json/state"

    # Build the JSON payload for the current LED
    json_data = {
        "seg": [
            {
                "start": 0,
                "stop": NUM_LEDS,
                "i": [[current_led, *color]],
                "on": True
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(api_endpoint, json=json_data) as response:
            if response.status == 200:
                print(f"Successfully lit up LED {current_led} with color {color}")
            else:
                print(f"Failed to light up LED {current_led}: {response.status} - {await response.text()}")

async def set_leds_fade(led_indices, color, fade_steps=10, fade_delay=0.001):
    """
    Light up multiple LEDs with a fade effect.
    Args:
        led_indices (list): List of LED indices to light up.
        color (tuple): The RGB color of the LEDs (e.g., (255, 0, 0)).
        fade_steps (int): Number of steps for fading out.
        fade_delay (float): Delay between fade steps in seconds.
    """
    
    print(f"Light Fade Function Start = {time.perf_counter()}")
    
    api_endpoint = f"http://{WLED_IP}/json/state"

    for step in range(fade_steps, -1, -1):
        adjusted_color = tuple(int(c * step / fade_steps) for c in color)

        # Create a full LED payload for the entire strip
        full_led_payload = [rgb_to_hex((0, 0, 0))] * NUM_LEDS
        for index in led_indices:
            full_led_payload[index] = rgb_to_hex(adjusted_color)

        # Build the JSON payload with the entire strip state
        json_data = {
            "seg": [
                {
                    "start": 0,
                    "stop": NUM_LEDS,
                    "i": full_led_payload,
                    "on": True
                }
            ]
        }
        print(f"HTTP Session Start = {time.perf_counter()}")
        async with aiohttp.ClientSession() as session:
            
            print(f"HTTP POST Start = {time.perf_counter()}")
            async with session.post(api_endpoint, json=json_data) as response:
                if response.status != 200:
                    print(f"Failed to set LEDs: {response.status} - {await response.text()}")
            print(f"HTTP POST End = {time.perf_counter()}")
                
        await asyncio.sleep(fade_delay)
        print(f"HTTP Session End = {time.perf_counter()}")
        print(f"Light Fade Function End = {time.perf_counter()}")

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
        if dot_product > 0.98:  # Adjust threshold to control ray match sensitivity
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

                        # Debugging: Visualize the line
                        if ENABLE_DEBUG:
                            visualize_line(position, direction)

                        # Calculate which LEDs to light up
                        print(f"LED Light Start = {time.perf_counter()}")
                        
                        lit_leds = calculate_leds_to_light(position, direction, led_positions)
                        

                        # Debugging: Output lit LEDs
                        if ENABLE_DEBUG and lit_leds:
                            print(f"Lit LEDs: {lit_leds}")

                        # Light up the LEDs with fade during load
                        if choice == "load" and lit_leds:
                            await set_leds_fade(lit_leds, [255, 0, 0])  # Red color
                        elif lit_leds:
                            for led in lit_leds:
                                await set_leds(led, [255, 0, 0])  # Red color
                                
                        print(f"LED Light End = {time.perf_counter()}")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        openvr.shutdown()
# endregion

if __name__ == "__main__":
    asyncio.run(main())
