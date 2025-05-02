import tkinter as tk
import paho.mqtt.client as mqtt
import uuid

TANK_ID = "0xdca632bf930a"  # Remplace par le bon ID si besoin
BROKER = "192.168.0.125" # Remplace par l'IP de ton broker
PORT = 1883
TOPIC_SOUND = f"tanks/{TANK_ID}/sound"

client = mqtt.Client(f"remote_{uuid.uuid4()}")
client.connect(BROKER, PORT)
client.loop_start()

def send(command):
    print(f"[TELECOMMANDE] Envoi: {command}")
    client.publish(f"tanks/{TANK_ID}/command", command)

def play_sound(sound):
    print(f"[TELECOMMANDE] Son: {sound}")
    client.publish(TOPIC_SOUND, sound)

root = tk.Tk()
root.title(f"Remote Control")

btn_conf = {"width": 15, "height": 2, "pady": 5}

tk.Button(root, text="Avancer", command=lambda: send("UP"), **btn_conf).grid(row=0, column=1)
tk.Button(root, text="Gauche", command=lambda: send("LEFT"), **btn_conf).grid(row=1, column=0)
tk.Button(root, text="STOP", command=lambda: send("STOP"), bg="red", fg="white", **btn_conf).grid(row=1, column=1)
tk.Button(root, text="Droite", command=lambda: send("RIGHT"), **btn_conf).grid(row=1, column=2)
tk.Button(root, text="Reculer", command=lambda: send("DOWN"), **btn_conf).grid(row=2, column=1)
tk.Button(root, text="Feu", command=lambda: send("FIRE"), bg="orange", **btn_conf).grid(row=3, column=1)
tk.Button(root, text="Scan QR", command=lambda: send("SCAN_QR"), bg="lightgreen", **btn_conf).grid(row=5, column=1)

# NEW: Sound Buttons
sound_row = 4
tk.Button(root, text="SUI", command=lambda: play_sound("sui"), bg="purple", fg="white", **btn_conf).grid(row=sound_row, column=0)
tk.Button(root, text="DISCO", command=lambda: play_sound("disco"), bg="blue", fg="white", **btn_conf).grid(row=sound_row, column=2)

tk.Button(root, text="Quitter", command=root.quit, bg="black", fg="white", **btn_conf).grid(row=6, column=1)

root.mainloop()
client.loop_stop()
client.disconnect()

