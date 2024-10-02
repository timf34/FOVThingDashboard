"""
A temporary script to simulate an FOV Tablet and send similar messages to a topic.

What do our devices do? What information do they send to which topics at what frequency?
"""
import json
import random
import time

from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials

CERT_PATH = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-certificate.pem.crt"
PRIVATE_KEY_PATH = "./aws-iot-certs/fov-dashboard-sydney-client/fov-dashboard-client-sydney-1-private.pem.key"
ROOT_CA_PATH = "./aws-iot-certs/fov-dashboard-sydney-client/AmazonRootCA1.pem"
ENDPOINT = "a3lkzcadhi1yzr-ats.iot.ap-southeast-2.amazonaws.com"


def initialize_iot_manager() -> IOTClient:

    iot_context = IOTContext()

    iot_credentials = IOTCredentials(
        cert_path=CERT_PATH,
        client_id="FOVTablet-Simulator",
        endpoint=ENDPOINT,
        priv_key_path=PRIVATE_KEY_PATH,
        ca_path=ROOT_CA_PATH
    )

    return IOTClient(iot_context, iot_credentials, publish_topic="hello")


def main():
    iot_client = initialize_iot_manager()
    iot_client.connect()

    iot_client.publish(topic="ap-southeast-2/marvel/fov-marvel-tablet-test/version",
                       payload=json.dumps({"Version": "1.1.0"}))

    while True:
        temperature = round(random.uniform(50, 100), 2)  # Generate a float with 2 decimal places
        battery = random.randint(0, 100)

        temp_payload = json.dumps({"Temperature": temperature})
        battery_payload = json.dumps({"Battery": battery})

        iot_client.publish(topic="ap-southeast-2/marvel/fov-marvel-tablet-test/temperature", payload=temp_payload)
        iot_client.publish(topic="ap-southeast-2/marvel/fov-marvel-tablet-test/battery", payload=battery_payload)

        time.sleep(5)


if __name__ == "__main__":
    main()
