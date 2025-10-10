import json, queue, re, sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import subprocess

MODEL_PATH = "/home/andre/vosk/model"  # update if different
SAMPLE_RATE = 16000
DEVICE = None   # None = default input. Or set ALSA index like 1.

COMMANDS = {
    r"\b.*ights\s*on\b": "LIGHTS_ON",
    r"\b.*ights\s*off\b": "LIGHTS_OFF",
    r"toggle": "LIGHTS_OFF",
    r"\b.*rightness\s*(up)\b": "BRIGHTNESS_UP",
    r"\b.*rightness\s*(down)\b": "BRIGHTNESS_DOWN",
    r"\bwhiteness\s*(up)\b": "BRIGHTNESS_UP",
    r"\bwhiteness\s*(down)\b": "BRIGHTNESS_DOWN"
}

on_command = "mosquitto_pub -t zigbee2mqtt/lamp1/set -m '{ \"state\": \"ON\" }'"
off_command = "mosquitto_pub -t zigbee2mqtt/lamp1/set -m '{ \"state\": \"OFF\" }'"

def toggle_lights(light_num):
    
    toggle_command = "mosquitto_pub -t zigbee2mqtt/lamp" + str(light_num) + "/set -m '{ \"state\": \"TOGGLE\" }'"
    # Execute the command
    try:
        subprocess.run(toggle_command, shell=True, check=True)
        print("Command executed successfully: Light status toggled")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

def adjust_brightness(factor, light_num):
    command = "mosquitto_pub -t zigbee2mqtt/lamp" + str(light_num) + "/set -m '{\"brightness_step\": " + str(factor) + ", \"transition\": 1 }' "
    

    try:
        subprocess.run(command, shell=True, check=True)
        print("Command executed successfully: Brightness adjusted for lamp" + str(light_num))
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")



def detect_command(text):
    t = text.lower()
    for pattern, cmd in COMMANDS.items():
        if re.search(pattern, t):
            return cmd
    return None

def handle_command(cmd):
    if cmd == "LIGHTS_ON":
        print("Turning lights ON")
        toggle_lights(1)
        toggle_lights(2)
        toggle_lights(3)
    elif cmd == "LIGHTS_OFF":
        print("Turning lights OFF")
        toggle_lights(1)
        toggle_lights(2)
        toggle_lights(3)
    elif cmd == "BRIGHTNESS_DOWN":
        print("Turning brightness down")
        adjust_brightness(-80, 1)
        adjust_brightness(-80, 2)
        adjust_brightness(-80, 3)
    elif cmd == "BRIGHTNESS_UP":
        print("Turning brightness up")
        adjust_brightness(80, 1)
        adjust_brightness(80, 2)
        adjust_brightness(80, 3)
    else:
        print("→ Unknown command:", cmd)



def main():
    print("Loading model…")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                           device=DEVICE, dtype='int16', channels=1,
                           callback=callback):
        print("Listening… say a command.")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    print("Heard:", text)
                    cmd = detect_command(text)
                    if cmd:
                        handle_command(cmd)
            else:
                # Partial results stream while speaking (optional)
                # partial = json.loads(rec.PartialResult()).get("partial", "")
                pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")

