import json
from datetime import datetime, timedelta


class Device:
    def __init__(self, name):
        self.name = name
        self.wifi_connected = False
        self.battery_charge = None
        self.temperature = None
        self.firmware_version = None
        self.last_message_time = None

    def update(self, message_type, value):
        self.last_message_time = datetime.now()

        if message_type == 'version':
            self.firmware_version = value  # Handle version as a plain string (it's not sent as a JSON)
            return

        # Parse the JSON string if it's not already a dictionary
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {value}")
                return

        if message_type == 'battery':
            print("Battery charge: ", value)
            self.battery_charge = float(value.get('Battery Percentage', 0))
        elif message_type == 'temperature':
            self.temperature = float(value.get('Temperature', 0))

    def check_wifi_status(self):
        if self.last_message_time and datetime.now() - self.last_message_time <= timedelta(seconds=61):
            self.wifi_connected = True
        else:
            self.wifi_connected = False

    def to_dict(self):
        return {
            'name': self.name,
            'wifiConnected': self.wifi_connected,
            'batteryCharge': self.battery_charge,
            'temperature': self.temperature,
            'firmwareVersion': self.firmware_version
        }
