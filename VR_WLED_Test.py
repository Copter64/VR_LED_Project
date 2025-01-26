import requests
import json
import time

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple to a HEX string.
    """
    return str('%02x%02x%02x' % rgb).upper()

def light_up_sequentially():
    # WLED device configuration
    wled_device_ip = "192.168.1.186"  # Replace with your WLED IP address
    api_endpoint = f"http://{wled_device_ip}/json/state"
    
    # Headers for the POST request
    headers = {'content-type': 'application/json'}
    
    # LED strip configuration
    num_leds = 358  # Total number of LEDs
    delay = 0.01  # Delay between lighting each LED in seconds
    
    # Loop to light up each LED one at a time

    for i in range(num_leds):
        # Create a strip where only one LED is lit
        strip = ["000000"] * num_leds
        strip[i] = rgb_to_hex((0, 0, 255))  # Set the current LED to blue
        
        # Build the JSON payload
        json_data = {"seg": {"i": strip}}

        # Send the POST request
        r = requests.post(api_endpoint, data=json.dumps(json_data), headers=headers)
        
        if r.status_code == 200:
            print(f"Successfully lit up LED {i}")
        else:
            print(f"Failed to light up LED {i}: {r.status_code}")
        
        # Wait for the delay before moving to the next LED
        time.sleep(delay)

def main():
    light_up_sequentially()

if __name__ == "__main__":
    main()
