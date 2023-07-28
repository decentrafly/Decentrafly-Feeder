import json
import logging
import os


loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=loglevel, format='%(message)s')


def load_config():
    config_file_path = os.path.expanduser("/etc/decentrafly/config.json")
    if os.path.isfile(config_file_path):
        config = json.load(open(config_file_path))
        return config
    else:
        return {}


default_config = {
    "DCF_CLIENT_ID": "notset",
    "DCF_IOT_TOPIC": "beast/ingest/0",
    "DCF_LOG_INTERVAL": "20",
    "DCF_MAX_INTERVAL": "1.0",
    "DCF_MAX_MESSAGE_SIZE": "100000",
    "DCF_READSB_HOST": "localhost",
    "DCF_READSB_PORT": "30005",
    "DCF_TRIGGER_SIZE": "50000",
    }

environment_config = {k: os.getenv(k) for k in default_config.keys()
                      if os.getenv(k) is not None}

effective_config = {**default_config, **load_config(), **environment_config}
