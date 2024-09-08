import os

USE_OMAR_CERTS: bool = False


class MQTTMergerConfig:
    def __init__(self):

        self.version_topic: str = "ap-southeast-2/marvel/fov-marvel-+/version"
        self.battery_topic: str = "ap-southeast-2/marvel/fov-marvel-+/battery"
        self.temperature_topic: str = "ap-southeast-2/marvel/fov-marvel-+/temperature"

        self.endpoint: str = "a13d7wu4wem7v1-ats.iot.ap-southeast-2.amazonaws.com"
        self.cert_path: str = "./aws-iot-certs/fov-dashboard-client-dublin-1-certificate.pem.crt"
        self.private_key_path: str = "./aws-iot-certs/fov-dashboard-client-dublin-1-private.pem.key"
        self.root_ca_path: str = "./aws-iot-certs/AmazonRootCA1.pem"
