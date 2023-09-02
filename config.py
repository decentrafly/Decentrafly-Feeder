import json
import logging
import os
import tempfile
import subprocess


loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
config_file_path = os.path.expanduser("/etc/decentrafly/config.json")


def write_to_file(path, content):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(content)
        tmp.close()
        return subprocess.call(['sudo', 'mv', tmp.name, path])


def load_config():
    if os.path.isfile(config_file_path):
        config = json.load(open(config_file_path))
        return config
    else:
        return {}

def write_config(updated_config):
    write_to_file(config_file_path,
                  json.dumps(updated_config, indent=2))


def persist_config_entry(k, v):
    current_config = load_config()
    current_config[k] = v
    return write_to_file(config_file_path, json.dumps(current_config,
                                                      indent=2))


def basic_logging():
    logging.basicConfig(level=loglevel, format='%(message)s')

default_config = {
    "DCF_LOG_INTERVAL": "20",

    "DCF_CA_FILE": '/etc/decentrafly/mtls-ca.crt',
    "DCF_CLIENT_CRT_FILE": '/etc/decentrafly/mtls-cert.crt',
    "DCF_CLIENT_KEY_FILE": '/etc/decentrafly/mtls-private.key',

    "DCF_CLIENT_ID": "notset",
    "DCF_IOT_TOPIC": "beast/ingest/0",
    "DCF_MAX_INTERVAL": "1.0",
    "DCF_MAX_MESSAGE_SIZE": "100000",
    "DCF_TRIGGER_SIZE": "50000",

    "DCF_READSB_HOST": "localhost",
    "DCF_READSB_PORT": "30005",

    "DCF_MAIN_DOMAIN": "api.decentrafly.org",

    "DCF_SECURE_ADSB_HOST": "localhost",
    "DCF_SECURE_ADSB_PORT": "40004",
    "DCF_SECURE_ADSB_HOSTNAME": "feed.decentrafly.org",
    }

environment_config = {k: os.getenv(k) for k in default_config.keys()
                      if os.getenv(k) is not None}

effective_config = {**default_config, **load_config(), **environment_config}

def ec(k):
    return effective_config.get(k.upper())
