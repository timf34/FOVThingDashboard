class FOVDashboardConfig:
    def __init__(self):

        # Wild card docs: https://docs.aws.amazon.com/iot/latest/developerguide/topics.html#topicfilters
        # self.version_topic: str = "ap-southeast-2/marvel/+/version"
        self.battery_topic: str = "ap-southeast-2/marvel/+/battery"
        self.temperature_topic: str = "ap-southeast-2/marvel/+/temperature"
        self.ota_topic: str = "ap-southeast-2/marvel/+/ota"

        self.endpoint: str = "a3lkzcadhi1yzr-ats.iot.ap-southeast-2.amazonaws.com"
        self.cert_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-certificate.pem.crt"
        self.private_key_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-private.pem.key"
        self.root_ca_path: str = "./aws-iot-certs/fov-dashboard-sydney-client/AmazonRootCA1.pem"

        self.version_topic: str = "eu-west-1/aviva/+/version"
        # self.battery_topic: str = "eu-west-1/aviva/+/battery"
        # self.temperature_topic: str = "eu-west-1/aviva/+/temperature"
        # self.ota_topic: str = "eu-west-1/aviva/+/ota"

        # self.endpoint: str = "a3lkzcadhi1yzr-ats.iot.eu-west-1.amazonaws.com"
        # self.cert_path: str = "./aws-iot-certs/fov-dashboard-dublin-client/certificate.pem.crt"
        # self.private_key_path: str = "./aws-iot-certs/fov-dashboard-dublin-client/private.pem.key"
        # self.root_ca_path: str = "./aws-iot-certs/fov-dashboard-dublin-client/AmazonRootCA1.pem"

        # ---- latency ---------------------------------------------------- #
        # Ping is published to a device‑specific topic;       example:
        # All tablets subscribe to ONE “publish” topic. We send pings there.
        # Tablets echo back on a (still shared) echo topic.
        # self.latency_ping_topic: str  = "dalymount_IRL/pub"
        self.latency_ping_topic: str  = "marvel_AUS/ai_pub"
        self.latency_echo_topic: str  = "esp32/echo"