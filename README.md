
# Simple Pi Camera Streamer

This project streams video from a Raspberry Pi camera using `picamera2` and `ffmpeg`.  
Control camera settings remotely via MQTT messages.

---

## Features

- Streams raw video from Pi Camera to a TCP port using FFmpeg.
- Control camera parameters like gain, exposure, focus, and modes via MQTT.
- Graceful shutdown on errors or keyboard interrupt (Ctrl+C).

---

## Requirements

- Raspberry Pi with Pi Camera and `picamera2` library installed.
- `ffmpeg`
- MQTT broker (e.g., Mosquitto)
- Python dependencies (`cv2`, `picamera2`, `paho-mqtt`, etc.)

---

## Installation Notes

- On Raspberry Pi OS or Debian-based systems, install the dependencies using:

  ```bash
  sudo apt update
  sudo apt install libcamera-apps libcamera-dev python3-paho-mqtt python3-opencv python3-picamera2 ffmpeg
  sudo apt install mosquitto
  sudo systemctl enable mosquitto
  sudo systemctl start mosquitto


## Usage

1. Start your MQTT broker (e.g., Mosquitto).

2. Run the main program:

   ```bash
   python3 main.py


## Control parameters

   ```bash
   mosquitto_pub -h 192.168.20.113 -t "picam/controls/gain" -m "1"

## Play Video

   ```bash
   ffplay -fflags nobuffer -flags low_delay -framedrop -strict experimental -f h264 tcp://192.168.20.113:8811
