import paho.mqtt.client as mqtt
import uuid
import RPi.GPIO as GPIO
import time
import threading
from move import setup as setup_motors, move, motorStop
from fire import fireBlast
import InfraLib
from LED import LED
import cv2
from pyzbar.pyzbar import decode

TANK_ID = hex(uuid.getnode())
# BROKER = "test.mosquitto.org"
BROKER = "192.168.0.125"
PORT = 1883
led = LED()
speed = 60
IR_PIN = 15
LINE_MIDDLE = 16
color = "RED"


TOPIC_BASE = f"tanks/{TANK_ID}"
TOPICS = {
    "init": f"{TOPIC_BASE}/init",
    "command": f"{TOPIC_BASE}/command",
    "shots": f"{TOPIC_BASE}/shots",
    "shots_out": f"{TOPIC_BASE}/shots/out",
    "shots_in": f"{TOPIC_BASE}/shots/in",
    "flag": f"{TOPIC_BASE}/flag",
    "qr": f"{TOPIC_BASE}/qr_code",
    "sound": f"{TOPIC_BASE}/sound"
}

if color == "RED":
        led.colorWipe(255, 0, 0)  # red

if color == "BLUE":
     led.colorWipe(0, 0, 255)  # blue

client = mqtt.Client(f"rasptank_{TANK_ID}")
led.colorWipe(0, 0, 255)

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected")
    for topic in TOPICS.values():
        client.subscribe(topic)
    client.publish("init", f"INIT {TANK_ID}")
    client.publish(TOPICS["sound"], "start_engine")



def scan_qr_code(image):
    decoded_objects = decode(image)
    for obj in decoded_objects:
        data = obj.data.decode('utf-8')
        print(f"QR Code detected: {data}")
        return data
    print(" No QR Code detected.")
    return None
def capture_and_scan_qr():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print(" Failed to capture image.")
        return None
    return scan_qr_code(frame)

def on_message(client, userdata, msg):
    cmd = msg.payload.decode()
    print(f"Command: {cmd}")

    if msg.topic == TOPICS["command"]:
        if cmd == "UP": move(speed, 'forward', 'no')
        elif cmd == "DOWN": move(speed, 'backward', 'no')
        elif cmd == "LEFT": move(speed, 'no', 'left')
        elif cmd == "RIGHT": move(speed, 'no', 'right')
        elif cmd == "STOP": motorStop()
        elif cmd == "FIRE":
            fireBlast()
            client.publish(TOPICS["sound"], "missile")
        elif cmd == "SCAN_QR":
            qr_data = capture_and_scan_qr()
            if qr_data:
                client.publish(TOPICS["qr"], qr_data)
                print(f"QR Published: {qr_data}")
            else:
                print(" No QR detected.")

        
        

def ir_callback(channel):
    shooter_id = InfraLib.getSignal(IR_PIN)
    print(shooter_id); #get rid of --> for now returns None
    if shooter_id:
        client.publish(TOPICS["shots"], f"SHOT_BY {shooter_id}")

def zone_callback(channel):
    if GPIO.input(LINE_MIDDLE) == 0:
        client.publish(TOPICS["flag"], "ENTER_FLAG_AREA")
    else:
        client.publish(TOPICS["flag"], "EXIT_FLAG_AREA")

def setup():
    setup_motors()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(IR_PIN, GPIO.FALLING, callback=ir_callback, bouncetime=150)
    GPIO.setup(LINE_MIDDLE, GPIO.IN)
    GPIO.add_event_detect(LINE_MIDDLE, GPIO.BOTH, callback=zone_callback, bouncetime=200)

def run():
    setup()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_forever()

if __name__ == "__main__":
    run()


