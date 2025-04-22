"""
A temporary script to simulate an FOV Tablet and send similar messages to a topic.

What do our devices do? What information do they send to which topics at what frequency?
"""
import json
import random
import time

from aws_iot.IOTClient import IOTClient
from aws_iot.IOTContext import IOTContext, IOTCredentials
from config import FOVDashboardConfig

config = FOVDashboardConfig()


def initialize_iot_manager() -> IOTClient:

    iot_context = IOTContext()

    iot_credentials = IOTCredentials(
        cert_path=config.cert_path,
        client_id="FOVTablet-Simulator",
        endpoint=config.endpoint,
        priv_key_path=config.private_key_path,
        ca_path=config.root_ca_path
    )

    return IOTClient(iot_context, iot_credentials)


def main():
    iot_client = initialize_iot_manager()
    iot_client.connect()

    iot_client.publish(topic="eu-west-1/aviva/fov-marvel-tablet-test-2/version",
                       payload=json.dumps({"Version": "1.1.0"}))

    while True:
        temperature = round(random.uniform(50, 100), 2)  # Generate a float with 2 decimal places
        battery = random.randint(0, 100)

        temp_payload = json.dumps({"Temperature": temperature})
        battery_payload = json.dumps({"Battery Percentage": battery})

        iot_client.publish(topic="eu-west-1/aviva/fov-marvel-tablet-test-2/temperature", payload=temp_payload)
        iot_client.publish(topic="eu-west-1/aviva/fov-marvel-tablet-test-2/battery", payload=battery_payload)

        time.sleep(5)


if __name__ == "__main__":
    main()
