from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

def send_mqtt(lamp_id, payload):
    topic = f"zigbee2mqtt/lamp{lamp_id}/set"
    command = ["mosquitto_pub", "-t", topic, "-m", payload]
    subprocess.run(command)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    lamp_id = data.get('lamp_id')
    action = data.get('action') # 'state', 'brightness', or 'color_temp'
    value = data.get('value')

    if action == 'state':
        payload = f'{{"state": "{value}"}}'
    elif action == 'brightness':
        payload = f'{{"brightness": {value}}}'
    elif action == 'color_temp':
        payload = f'{{"color_temp": {value}}}'
    
    send_mqtt(lamp_id, payload)
    return {"status": "success"}

if __name__ == '__main__':
    # host='0.0.0.0' makes it accessible to the local network
    app.run(host='0.0.0.0', port=5000)
