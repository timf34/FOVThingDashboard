class FOVDashboardConfig:
    def __init__(self):

        # Wild card docs: https://docs.aws.amazon.com/iot/latest/developerguide/topics.html#topicfilters
        self.version_topic: str = "ap-southeast-2/marvel/+/version"
        self.battery_topic: str = "ap-southeast-2/marvel/+/battery"
        self.temperature_topic: str = "ap-southeast-2/marvel/+/temperature"

        self.endpoint: str = "a3lkzcadhi1yzr-ats.iot.ap-southeast-2.amazonaws.com"
        self.cert_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-certificate.pem.crt"
        self.private_key_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-private.pem.key"
        self.root_ca_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-public.pem.key"
