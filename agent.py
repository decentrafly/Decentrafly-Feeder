from awscrt import mqtt
from config import effective_config
import json
import logging
import pubsub
import subprocess
import time

logger = logging.getLogger("agent")


class Agent:
    def __init__(self,
                 client_id,
                 cert_path,
                 private_key_path,
                 ca_path):
        self.mqtt_connection = pubsub.mqtt_connection_from_certfiles(client_id + "-agent",
                                                                     cert_path,
                                                                     private_key_path,
                                                                     ca_path)
        self.client_id = client_id

    def secure_tunnel_request(self, payload):
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
        topic = "$aws/things/{}/tunnels/notify".format(self.client_id)
        subscribe_future, packet_id = self.mqtt_connection.subscribe(
            topic=topic,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=lambda topic, payload, dup, qos, retain, **kwargs:
            self.secure_tunnel_request(payload))
        subscribe_result = subscribe_future.result()
        logger.info("Subscribed to {} with qos {}".format(topic, str(subscribe_result['qos'])))

    def run(self):
        self.listen_for_remote_access_request()
        while True:
            time.sleep(600)


def run():
    if ('DCF_REMOTE_ACCESS' in effective_config and effective_config['DCF_REMOTE_ACCESS'] == "True"):
        logger.info("Remote access is enabled!")
        agent = Agent(effective_config['DCF_CLIENT_ID'],
                      "/etc/decentrafly/cert.crt",
                      "/etc/decentrafly/private.key",
                      "/etc/decentrafly/ca.crt")
        agent.run()
    else:
        logger.info("Remote access is turned off.")
        while True:
            time.sleep(600)
