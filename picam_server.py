import cv2
import subprocess
import signal
import sys
import threading
import json
from picamera2 import Picamera2


class PiCamServer:
    def __init__(self, config_file='video_config.json'):
        self._stop_event = threading.Event()

        self.load_config(config_file)

        self.picam2 = Picamera2()
        self.process = None

        self.running = False

        self.setup_camera()
        self.register_cleanup()

    def load_config(self, filename):
        with open(filename, 'r') as f:
            config = json.load(f)
            self.fps = config['fps']
            self.resolution = tuple(config['resolution'])
            self.bitrate = config['bitrate']

    def setup_camera(self):
        video_config = self.picam2.create_video_configuration(
            main={"size": self.resolution, "format": "RGB888"},
            controls={"FrameRate": self.fps}
        )
        self.picam2.configure(video_config)

        self.picam2.start()
        self.picam2.set_controls({
            "AeExposureMode": 0,
            "ExposureTimeMode": 0,
            "AnalogueGainMode": 0,
            "AnalogueGain": 5,
            "ExposureTime": 33333,
            "LensPosition": 11,
        })

    def start_ffmpeg(self):
        cmd = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'h264_v4l2m2m',
            '-b:v', self.bitrate,
            '-f', 'h264',
            'tcp://0.0.0.0:8811?listen=1'
        ]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def stop(self):
        print("[PiCamServer] Stopping...")
        self._stop_event.set()

    def run(self):
        self.start_ffmpeg()
        self.running = True

        try:
            while not self._stop_event.is_set():
                frame = self.picam2.capture_array()
                metadata = self.picam2.capture_metadata()

                exposure_us = metadata.get("ExposureTime", 0)
                gain = metadata.get("AnalogueGain", 0)
                focus = metadata.get("LensPosition", 0)
                exposure_ms = exposure_us / 1000.0

                overlay_text = f"Exp: {exposure_ms:.1f}ms  Gain: {gain:.2f}  Focus: {focus:.2f}"
                cv2.putText(frame, overlay_text, (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                self.process.stdin.write(frame.tobytes())
                self.process.stdin.flush()

        except (BrokenPipeError, IOError) as e:
            print(f"[PiCamServer] Client disconnected or pipe broken: {e}")
            self._stop_event.set()

        except Exception as e:
            print(f"[PiCamServer] Exception: {e}")
            self._stop_event.set()

        finally:
            self.cleanup()
            self.running = False

    def set_exposure_mode(self, mode: int):
        self.picam2.set_controls({"ExposureTimeMode": mode})

    def set_exposure(self, exposure_us):
        if 100 <= exposure_us <= 1000000:
            self.picam2.set_controls({"ExposureTime": exposure_us})

    def set_gain(self, gain):
        if 1.0 <= gain <= 15.0:
            self.picam2.set_controls({"AnalogueGain": gain})

    def set_focus(self, focus):
        if 0.0 <= focus <= 15.0:
            self.picam2.set_controls({"LensPosition": focus})

    def set_gain_mode(self, mode: int):
        self.picam2.set_controls({"AnalogueGainMode": mode})

    def register_cleanup(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, *args):
        print("[PiCamServer] Cleaning up...")
        try:
            if self.process:
                if self.process.stdin:
                    try:
                        self.process.stdin.close()
                    except Exception as e:
                        print(f"[PiCamServer] Error closing ffmpeg stdin: {e}")
                self.process.wait()
        except Exception as e:
            print(f"[PiCamServer] FFmpeg cleanup failed: {e}")
        finally:
            try:
                self.picam2.stop_preview()
            except RuntimeError:
                pass
            except Exception as e:
                pass    
            try:
                self.picam2.stop()
            except Exception as e:
                pass    
            try:
                self.picam2.close()
            except Exception as e:
                pass
    
if __name__ == "__main__":
    server = PiCamServer()
    server.run()
