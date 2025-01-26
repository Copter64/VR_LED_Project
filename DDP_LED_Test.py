import socket
import time

# WLED Configuration
WLED_IP = "192.168.1.186"  # Replace with your WLED IP
WLED_PORT = 4048  # Default DDP port for WLED
NUM_LEDS = 358  # Total number of LEDs
DELAY = 0.05  # Delay between updates (seconds)
FADE_FACTOR = .99  # How much brightness fades per step (0.8 = 80% brightness retained)

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

def light_up_with_fade():
    """
    Sequentially light up LEDs with a fading effect using DDP packets.
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Initialize a buffer to track brightness levels for each LED
    led_brightness = [[0, 0, 0] for _ in range(NUM_LEDS)]  # Start with all LEDs off

    try:
        while True:
            for i in range(NUM_LEDS):
                # Light up the current LED with full brightness (Blue: GBR = 0, 0, 255)
                led_brightness[i] = [0, 0, 255]

                # Apply the fade effect to all LEDs
                for j in range(NUM_LEDS):
                    led_brightness[j] = [
                        max(0, int(led_brightness[j][0] * FADE_FACTOR)),  # Fade Green
                        max(0, int(led_brightness[j][1] * FADE_FACTOR)),  # Fade Blue
                        max(0, int(led_brightness[j][2] * FADE_FACTOR))   # Fade Red
                    ]

                # Create pixel data from the brightness buffer
                pixel_data = bytearray()
                for color in led_brightness:
                    pixel_data.extend(color)

                # Create the DDP packet
                packet = create_ddp_packet(pixel_data)

                # Send the packet to the WLED device
                sock.sendto(packet, (WLED_IP, WLED_PORT))
                print(f"Lit up LED {i} with fade effect")

                # Wait for the delay before moving to the next LED
                time.sleep(DELAY)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        sock.close()

def main():
    light_up_with_fade()

if __name__ == "__main__":
    main()
