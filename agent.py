from awscrt import mqtt
from config import ec
from ip import get_device_ips
import asyncio
import json
import logging
import pubsub
import subprocess
import time

logger = logging.getLogger("agent")

TOPIC_DEVICE_INFO = '$aws/rules/prod_feeder/device/info'


class Agent:
    def __init__(self,
                 client_id,
                 cert_path,
                 private_key_path,
                 ca_path):
        self.mqtt_connection = pubsub.mqtt_connection_from_certfiles(client_id,
                                                                     cert_path,
                                                                     private_key_path,
                                                                     ca_path)
        self.client_id = client_id

    def secure_tunnel_request(self, payload):
        if ec('DCF_REMOTE_ACCESS') != "True":
            # Double safe-guard to prevent unwanted remote access
            raise Exception("Remote access is disabled.")

        request = json.loads(payload)
        if "destination" != request['clientMode']:
            logger.error("Remote requested secure tunnel with mode %s", request['clientMode'])
            return
        if ["SSH"] != request['services']:
            logger.error("Remote requested secure tunnel for services %s", request['services'])
            return

        logger.info("Initiating remote access secure tunnel")
        subprocess.Popen(["localproxy",
                          "-t", request['clientAccessToken'],
                          "-r", request['region'],
                          "-d", "localhost:22"])

    def listen_for_remote_access_request(self):
        if ec('DCF_REMOTE_ACCESS') != "True":
            # Double safe-guard to prevent unwanted remote access
            raise Exception("Remote access is disabled.")

        topic = "$aws/things/{}/tunnels/notify".format(self.client_id)
        subscribe_future, packet_id = self.mqtt_connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=lambda topic, payload, dup, qos, retain, **kwargs:
            self.secure_tunnel_request(payload))
        subscribe_result = subscribe_future.result()
        logger.info("Subscribed to {} with qos {}".format(topic, str(subscribe_result['qos'])))

    async def update_ip_information(self):
        while True:
            try:
                device_ips = get_device_ips()
                self.mqtt_connection.publish(
                    topic=TOPIC_DEVICE_INFO,
                    payload=json.dumps(
                        {
                            "device_id": ec('DCF_FEEDER_ID'),
                            "ip": device_ips[0],
                            "time": time.time(),
                            "device_token": ec('DCF_FEEDER_TOKEN')
                        }
                    ),
                    qos=mqtt.QoS.AT_MOST_ONCE)
                print("Updated device info")
            except Exception as e:
                print("Failed to update device info")
                raise e

            await asyncio.sleep(120)

    def run(self):
        # For uses that opt-in to remote access, we wait for connection requests
        if ec('DCF_REMOTE_ACCESS') == "True":
            logger.info("Remote access is enabled!")
            self.listen_for_remote_access_request()

        loop = asyncio.get_event_loop()
        task = loop.create_task(self.update_ip_information())

        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            print("Cancelled")
            exit(2)
        except Exception as e:
            print("Exception was raised")
            print(e)
            exit(2)


def run():
    agent = Agent("beastdatafeed-" + ec('DCF_FEEDER_ID') + "-agent",
                  "/etc/decentrafly/cert.crt",
                  "/etc/decentrafly/private.key",
                  "/etc/decentrafly/ca.crt")
    agent.run()
