# WLED Configuration
WLED_IP = "192.168.1.114"  # Replace with your WLED IP
NUM_LEDS = 358  # Total number of LEDs on the strip

# SteamVR Settings
POINTER_ACCURACY = .9999  # Must be a float less than 1, the larger the number the more precise the virtual pointer is, the smaller lights more LEDs at a time

# File to save/load mapped LED positions
LED_MAPPING_FILE = "led_mapping.json"

# Debugging and Visualization Options
ENABLE_DEBUG = True
ENABLE_VISUALIZATION = False

FADETIME = 10  # Time in seconds for LED fade transitions
FADEDELAY = 0.05  # Delay in seconds between each fade step (Frame rate for fading)