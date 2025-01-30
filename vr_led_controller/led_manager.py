import json
import numpy as np
from collections import defaultdict
from config import NUM_LEDS, LED_MAPPING_FILE, POINTER_ACCURACY

# Shared state for LED management
led_state = defaultdict(lambda: [0, 0, 0, 0])  # Tracks [R, G, B, fade_steps] for each LED

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
    from config import WLED_IP
    import socket
    import asyncio

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
    import asyncio

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