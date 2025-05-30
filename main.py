import threading
import time
import sys
from mqtt_server import MqttControlServer
from picam_server import PiCamServer

def main():
    cam = PiCamServer()
    mqtt = MqttControlServer()

    mqtt.register_callback("gain", lambda val: cam.set_gain(float(val)))
    mqtt.register_callback("exposure", lambda val: cam.set_exposure(int(val)))
    mqtt.register_callback("gain_mode", lambda val: cam.set_gain_mode(int(val)))
    mqtt.register_callback("exposure_mode", lambda val: cam.set_exposure_mode(int(val)))
    mqtt.register_callback("focus", lambda val: cam.set_focus(int(val)))

    # Run cam and mqtt in separate threads so both run concurrently
    cam_thread = threading.Thread(target=cam.run, daemon=True)
    mqtt_thread = threading.Thread(target=mqtt.run, daemon=True)

    cam_thread.start()
    mqtt_thread.start()

    try:
        while cam_thread.is_alive() and mqtt_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        cam.stop()
        mqtt.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
