import socket
import time

# WLED Configuration
WLED_IP = "192.168.1.186"  # Replace with your WLED IP
WLED_PORT = 4048  # Default DDP port for WLED
NUM_LEDS = 358  # Total number of LEDs
DELAY = 0.01  # Delay between updates

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

def light_up_sequentially():
    """
    Sequentially light up LEDs using DDP packets.
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            for i in range(NUM_LEDS):
                # Create pixel data: All LEDs off except one
                pixel_data = bytearray([0, 0, 0] * NUM_LEDS)
                pixel_data[i * 3:i * 3 + 3] = [0, 0, 255]  # Blue color for the current LED

                # Create the DDP packet
                packet = create_ddp_packet(pixel_data)

                # Send the packet to the WLED device
                sock.sendto(packet, (WLED_IP, WLED_PORT))
                print(f"Lit up LED {i} with blue color")

                # Wait for a delay before the next LED
                time.sleep(DELAY)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        sock.close()

def main():
    light_up_sequentially()

if __name__ == "__main__":
    main()
