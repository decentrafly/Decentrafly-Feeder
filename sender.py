import beast
import json
import os
import pubsub
import socket
import time
from awscrt import mqtt


def load_config():
    config_file_path = os.path.expanduser("~/.config/decentrafly/config.json")
    if os.path.isfile(config_file_path):
        config = json.load(open(config_file_path))
        return config
    else:
        return {}


default_config = {
    "DCF_CLIENT_ID": "notset",
    "DCF_IOT_TOPIC": "beast/ingest/0",
    "DCF_LOG_INTERVAL": "20",
    "DCF_MAX_INTERVAL": "1.5",
    "DCF_MAX_MESSAGE_SIZE": "100000",
    "DCF_READSB_HOST": "localhost",
    "DCF_READSB_PORT": "30005",
    "DCF_TRIGGER_SIZE": "50000",
    }

environment_config = {k: os.getenv(k) for k in default_config.keys()
                      if os.getenv(k) is not None}

effective_config = {**default_config, **load_config(), **environment_config}

aws_iot_topic = effective_config['DCF_IOT_TOPIC']
client_id = effective_config['DCF_CLIENT_ID']
log_interval = int(effective_config['DCF_LOG_INTERVAL'])
max_interval = float(effective_config["DCF_MAX_INTERVAL"])
max_message_size = int(effective_config["DCF_MAX_MESSAGE_SIZE"])
readsb_host = effective_config['DCF_READSB_HOST']
readsb_port = int(effective_config['DCF_READSB_PORT'])
trigger_size = int(effective_config["DCF_TRIGGER_SIZE"])

class Sender:
    def __init__(self,
                 client_id,
                 cert_path,
                 private_key_path,
                 ca_path):
        self.mqtt_connection = pubsub.mqtt_connection_from_certfiles(client_id,
                                                                     cert_path,
                                                                     private_key_path,
                                                                     ca_path)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.decoder = beast.Decoder()
        self.last_forward = time.time()
        self.connected = False
        self.messages_sent = 0
        self.bytes_received = 0
        self.bytes_forwarded = 0
        self.last_informative_log_at = 0

    def connect(self, host, port):
        print("Attempting connection to {}".format(host))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(120)
        self.sock.connect((host, port))
        print("Connected to readsb!")

    def forward(self):
        if (self.decoder.bytes_available() > trigger_size
           or time.time() - self.last_forward > max_interval):

            next_message = self.decoder.up_to_bytes(100000)
            if next_message:
                self.mqtt_connection.publish(topic=aws_iot_topic,
                                             payload=next_message,
                                             qos=mqtt.QoS.AT_LEAST_ONCE)
                self.messages_sent += 1
                self.bytes_forwarded += len(next_message)
                self.last_forward = time.time()

    def maybe_log_informative(self):
        if time.time() - self.last_informative_log_at > log_interval:
            self.last_informative_log_at = time.time()
            print("bytes received {} | bytes forwarded {} | messages {}"
                  .format(
                      self.bytes_received,
                      self.bytes_forwarded,
                      self.messages_sent))
        else:
            pass

    def run(self):
        while True:
            try:
                self.connect(readsb_host, readsb_port)
                connected = True
            except Exception:
                print("Connection failed. Backing off ...")
                time.sleep(25)
            while connected:
                try:
                    data = self.sock.recv(max_message_size)
                except Exception:
                    connected = False
                    break
                if len(data) > 0:
                    self.bytes_received += len(data)
                    self.decoder.read_bytes(data)
                    self.forward()
                else:
                    connected = False
                    break
                self.maybe_log_informative()


def run():
    sender = Sender(client_id,
                    os.path.expanduser("~/.config/decentrafly/cert.crt"),
                    os.path.expanduser("~/.config/decentrafly/private.key"),
                    os.path.expanduser("~/.config/decentrafly/ca.crt"))
    sender.run()
