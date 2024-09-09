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
        value = value.split(': ')[1] if ': ' in value else value
        if message_type == 'battery':
            print("Battery charge: ", value)
            self.battery_charge = float(value)
        elif message_type == 'temperature':
            self.temperature = float(value)
        elif message_type == 'version':
            self.firmware_version = value

    def check_wifi_status(self):
        if self.last_message_time and datetime.now() - self.last_message_time <= timedelta(seconds=10):
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
