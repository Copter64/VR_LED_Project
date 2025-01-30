# VR LED Controller

A Python project to control LED strips using a VR controller. This project maps the physical positions of LEDs in a 3D space using a VR controller and lights up LEDs based on the controller's position and orientation.

---

## Features
- **LED Mapping**: Map the physical positions of LEDs using a VR controller.
- **Real-Time Control**: Light up LEDs in real-time based on the VR controller's position and orientation.
- **Fading Effects**: Smooth fading effects for LEDs.
- **WLED Integration**: Send LED data to a WLED controller using the DDP protocol.
- **Customizable**: Easily configure LED count, IP address, and other settings.

---

## Requirements
- Python 3.8 or higher
- OpenVR (for VR controller support)
- WLED-compatible LED controller
- VR headset and controllers (e.g., HTC Vive, Oculus Rift)

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/vr_led_controller.git
cd vr_led_controller
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up WLED
- Ensure your WLED controller is connected to the same network as your computer.
- Update the `WLED_IP` in `config.py` with the IP address of your WLED controller.

---

## Usage

### 1. Map LED Positions
Run the following command to map the physical positions of your LEDs:
```bash
python -m vr_led_controller.main
```
- Choose `map` when prompted to start mapping.
- Point your VR controller at each LED and pull the trigger to save its position.

### 2. Control LEDs
After mapping, run the program again and choose `load` to load the saved LED positions. Point your VR controller to light up the LEDs.

### 3. Change Colors
- **Grip Button**: Change LED color to green.
- **Menu Button**: Change LED color to blue.
- **Trigger**: Change LED color to red.

---

## Configuration
Edit the `config.py` file to customize the following settings:
- `WLED_IP`: IP address of your WLED controller.
- `NUM_LEDS`: Total number of LEDs on your strip.
- `POINTER_ACCURACY`: Sensitivity of the VR controller's pointer.
- `current_color`: Default LED color.

---

## Project Structure
```
vr_led_controller/
│
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── helpers.py           # Utility functions
├── led_manager.py       # LED management and DDP protocol
├── vr_manager.py        # VR controller mapping and tracking
└── main.py              # Main program entry point
```

---

## Troubleshooting

### 1. ModuleNotFoundError
If you encounter `ModuleNotFoundError`, ensure the `vr_led_controller` package is in your `PYTHONPATH`. Add the following to your `.env` file:
```
PYTHONPATH=.
```

### 2. VR Controller Not Detected
- Ensure your VR headset and controllers are properly connected and tracked.
- Install the correct OpenVR drivers for your hardware.

### 3. WLED Not Responding
- Verify that the `WLED_IP` in `config.py` is correct.
- Ensure your WLED controller is powered on and connected to the network.

---

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments
- [OpenVR](https://github.com/ValveSoftware/openvr) for VR controller support.
- [WLED](https://kno.wled.ge/) for LED strip control.

---

## Contact
For questions or feedback, please open an issue on GitHub or contact Christopher at copter64@gmail.com.

---

Enjoy controlling your LEDs with VR! 🎮✨