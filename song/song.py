import paho.mqtt.client as mqtt
from playsound import playsound
import uuid

# --- CONFIGURATION ---
TANK_ID = hex(uuid.getnode())  # Tu peux aussi le mettre en dur si tu préfères
BROKER = "ton_ip_broker"  # Remplace par l'IP de ton broker
PORT = 1883

TOPIC_SOUND = f"tanks/{TANK_ID}/sound"
mqtt_client_id = f"sound_{TANK_ID}"

# --- MQTT Setup ---
try:
    # For paho-mqtt v2.0+
    client = mqtt.Client(client_id=mqtt_client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

except AttributeError:
    # Fallback for slightly older versions (e.g., 1.6) that might support v1 explicitly
    # or if VERSION2 doesn't exist in your installed version
    try:
        client = mqtt.Client(client_id=mqtt_client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
  
    except AttributeError:
       
         client = mqtt.Client(client_id=mqtt_client_id)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f" Connected to broker. Subscribed to: {TOPIC_SOUND}")
        client.subscribe(TOPIC_SOUND)
    else:
        print(f" Connection failed with code {rc}")

def on_message(client, userdata, message):
    msg = message.payload.decode()
    

    try:
        if msg == "start_engine":
            playsound("start_engine.mp3")
        elif msg == "accelerate":
            playsound("acceleration.mp3")
        elif msg == "missile":
            playsound("missile.mp3")
        elif msg == "sui":
            playsound("sui.mp3")
        elif msg == "disco":
            playsound("disco.mp3")
        else:
            print(" Unknown command.")
    except Exception as e:
        print(f"Failed to play sound: {e}")

# --- MAIN ---
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_forever()
