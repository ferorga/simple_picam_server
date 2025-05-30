import json
import threading
import paho.mqtt.client as mqtt

class MqttControlServer:
    def __init__(self, config_file="mqtt_config.json"):
        with open(config_file, "r") as f:
            self.config = json.load(f)
        self._stop_event = threading.Event()
        self.client = mqtt.Client(client_id=self.config.get("client_id", "mqtt_server"))
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.topic_prefix = self.config["topic_prefix"]
        self.callbacks = {}

    def disconnect(self):
        print("[MQTT] Disconnecting...")
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected with result code {rc}")
        for suffix in self.callbacks:
            topic = f"{self.topic_prefix}/{suffix}"
            client.subscribe(topic)
            print(f"[MQTT] Subscribed to {topic}")

    def _on_message(self, client, userdata, msg):
        topic_suffix = msg.topic.replace(self.topic_prefix + "/", "")
        payload = msg.payload.decode().strip()
        print(f"[MQTT] Received: {topic_suffix} = {payload}")
        if topic_suffix in self.callbacks:
            try:
                self.callbacks[topic_suffix](payload)
            except Exception as e:
                print(f"[MQTT] Callback error for {topic_suffix}: {e}")
        else:
            print(f"[MQTT] No callback registered for: {topic_suffix}")

    def register_callback(self, topic_suffix, callback):
        self.callbacks[topic_suffix] = callback

    def stop(self):
        print("[MqttControlServer] Stopping...")
        self._stop_event.set()

    def run(self):
        try:
            self.client.connect(self.config["broker"], self.config["port"], 60)
            self.client.loop_start()
            self._stop_event.wait()
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"[MqttControlServer] Error: {e}")
        finally:
            print("[MqttControlServer] Cleaned up")

if __name__ == "__main__":
    mqtt = MqttControlServer()
    mqtt.register_callback("gain", lambda val: print(f"Gain: {val}"))
    mqtt.register_callback("exposure", lambda val: print(f"Exposure: {val}"))
    mqtt.register_callback("gain_mode", lambda val: print(f"Gain Mode: {val}"))
    mqtt.register_callback("exposure_mode", lambda val: print(f"Exposure Mode: {val}"))
    mqtt.run()
