# VR LED Project

This repository contains a collection of projects and utilities for controlling addressable LEDs (such as WLED) using SteamVR-compatible VR controllers. The main focus is on mapping and controlling LEDs in real-time based on VR controller position and orientation, with additional features and experimental scripts for advanced LED effects and games.

---

## Main Project: VR LED Controller

A Python package to control LED strips using a VR controller. It allows you to map the physical positions of LEDs in 3D space and light them up interactively using your VR controller.

### Features
- **LED Mapping**: Map the physical positions of LEDs using a VR controller.
- **Real-Time Control**: Light up LEDs in real-time based on the VR controller's position and orientation.
- **Fading Effects**: Smooth fading effects for LEDs.
- **WLED Integration**: Send LED data to a WLED controller using the DDP protocol.
- **Customizable**: Configure LED count, IP address, and other settings.
- **Mini-Games**: Includes a Battleship game using the LED strip and VR controllers.

---

## Directory Structure & File Overview

```
VR_LED_Project/
│
├── vr_led_controller/           # Main package for VR LED control
│   ├── audio_manager.py         # Handles sound effects for games and feedback
│   ├── battleship.py            # Battleship game logic using LEDs and VR
│   ├── config.py                # Configuration (WLED IP, LED count, etc.)
│   ├── controller.py            # VR controller abstraction and input handling
│   ├── helpers.py               # Utility functions (math, orientation, etc.)
│   ├── led_manager.py           # LED state, DDP protocol, and effects
│   ├── main.py                  # Main entry point for mapping/controlling LEDs
│   ├── requirements.txt         # Python dependencies
│   ├── vr_manager.py            # VR system setup, mapping, and tracking
│   ├── sounds/                  # Sound files for feedback and games
│   └── readme.md                # Detailed documentation for the package
│
├── README.md                    # (This file) Project overview and usage
├── LICENSE                      # MIT License
├── CODE_OF_CONDUCT.md           # Contributor code of conduct
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
├── DDP_LED_Test.py              # Test script for DDP LED communication
├── VR_WLED_Test.py              # Test script for VR to WLED integration
└── led_mapping.json             # Example or generated LED mapping data
```

---

## Installation & Setup

1. **Clone the Repository**
   ```powershell
   git clone https://github.com/your-username/VR_LED_Project.git
   cd VR_LED_Project/vr_led_controller
   ```
2. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Configure WLED**
   - Ensure your WLED controller is on the same network.
   - Edit `config.py` and set `WLED_IP` to your controller's IP address.

---

## Usage

1. **Map LED Positions**
   ```powershell
   python -m vr_led_controller.main
   ```
   - Choose `map` when prompted.
   - Point your VR controller at each LED and pull the trigger to save its position.

2. **Control LEDs**
   - Run the program again and choose `load` to use the saved mapping.
   - Point your VR controller to light up LEDs in real time.

3. **Change LED Colors**
   - **Grip Button**: Green
   - **Menu Button**: Blue
   - **Trigger**: Red

4. **Play Battleship (Experimental)**
   - Run `battleship.py` for a VR LED-based Battleship game.

---

## Configuration
Edit `vr_led_controller/config.py` to adjust:
- `WLED_IP`: IP address of your WLED controller
- `NUM_LEDS`: Number of LEDs
- `POINTER_ACCURACY`: Pointer sensitivity
- `DEFAULT_COLOR`: Default LED color
- `FADETIME`, `FADEDELAY`: Fading effect parameters

---

## Troubleshooting
- **ModuleNotFoundError**: Ensure `vr_led_controller` is in your `PYTHONPATH`.
- **VR Controller Not Detected**: Check VR hardware and OpenVR drivers.
- **WLED Not Responding**: Verify `WLED_IP` and network connection.

---

## Contributing
- Fork the repository and create a new branch for your changes.
- Submit a pull request with a clear description.

---

## License
MIT License. See `LICENSE` for details.

---

## Contact
For questions or feedback, open an issue or contact Christopher at copter64@gmail.com.

---

Enjoy controlling your LEDs with VR! 🎮✨
