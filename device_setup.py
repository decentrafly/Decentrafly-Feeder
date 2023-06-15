from random import randrange
import json
import os
import re
import requests
import subprocess
import tempfile
import uuid


systemd_service_file = '''[Unit]
Description=MQTT Sender Service
After=network.target

[Service]
ExecStart=/usr/bin/decentrafly sender
Environment="PYTHONUNBUFFERED=1"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''


def write_to_file(path, content):
    f = open(os.path.expanduser(path), "w")
    f.write(content)
    f.close()


def client_id():
    return "beastdatafeed-" + str(uuid.uuid4())


def register_new_device(temporary_dir, device_attributes):
    thing_name = client_id()
    config_content = {"DCF_CLIENT_ID": thing_name,
                      "DCF_MQTT_HOST": "almfwrqpajske-ats.iot.us-east-1.amazonaws.com",
                      "DCF_IOT_TOPIC": "beast/ingest/" + str(randrange(1, 100))}

    aws_root_ca = requests.request('GET', "https://www.amazontrust.com/repository/AmazonRootCA1.pem")
    response = requests.request('POST',
                                "https://decentrafly.org/api/device/register",
                                json={"thing_name": thing_name,
                                      "attributes": device_attributes})
    data = response.json()
    write_to_file(os.path.join(temporary_dir, "cert.crt"), data['certs']['certificate'])
    write_to_file(os.path.join(temporary_dir, "private.key"), data['certs']['private_key'])
    write_to_file(os.path.join(temporary_dir, "ca.crt"), aws_root_ca.text)
    write_to_file(os.path.join(temporary_dir, "config.json"),
                  json.dumps(config_content, indent=2))


def parse_config_file(file_path):
    config_dict = {}
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=')
                    config_dict[key.strip()] = re.sub(r'[^a-zA-Z0-9_.,@/:#-]*', '', value.strip())
    return config_dict


def detect_device_attributes():
    adsb_config = parse_config_file("/boot/adsb-config.txt")
    required_keys = ['LATITUDE', 'LONGITUDE', 'USER', 'ALTITUDE']
    user_friendly_name = {
        "ALTITUDE": "the altitude of your antenna",
        "LATITUDE": "the latitude of your geo position",
        "LONGITUDE": "the longitude of your geo position",
        "USER": "your device nickname"
        }

    if any(key not in adsb_config for key in required_keys):
        print("\nSome information about your device could not be detected automatically")
        print("We kindly ask to provide this information, but you can leave it empty if you prefer.\n")

    for key in required_keys:
        if key not in adsb_config:
            value = input(f"Please provide a value for {user_friendly_name[key]}: ")
            adsb_config[key] = value
    return adsb_config


def self_setup():
    if not (os.path.isfile(os.path.expanduser("/etc/decentrafly/ca.crt"))
            and os.path.isfile(os.path.expanduser("/etc/decentrafly/cert.crt"))
            and os.path.isfile(os.path.expanduser("/etc/decentrafly/private.key"))):

        device_attributes = {}
        try:
            device_attributes = detect_device_attributes()
        except Exception:
            print("Unable to get device attributes, resuming without ...")

        print("\n\nPlease provide the sudo password to write config files to /etc/decentrafly")
        exit_code = 0
        exit_code += subprocess.call(['sudo', 'echo'])
        with tempfile.TemporaryDirectory() as tmpdirname:
            register_new_device(tmpdirname, device_attributes)
            exit_code += subprocess.call(['sudo', 'cp', '-r', tmpdirname, "/etc/decentrafly"])
            exit_code += subprocess.call(['sudo', 'chmod', '755', tmpdirname, "/etc/decentrafly"])
        if exit_code == 0:
            print("Setup done")
        else:
            print("Setup failed")
    else:
        print("Setup already done, I won't touch config or certificates")


def enable_service(executable):
    exit_code = 0

    print("Please provide the sudo password to install the service")
    exit_code += subprocess.call(['sudo', 'echo'])
    try:
        if subprocess.call(['sudo', 'which', 'systemctl']) != 0:
            print("Error: I need systemd to enable the service.")
            exit(1)
    except Exception:
        print("systemctl not found")
        exit(1)

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(systemd_service_file)
        tmp.close()
        exit_code += subprocess.call(['sudo', 'mv', tmp.name, "/usr/lib/systemd/system/decentrafly.service"])

    exit_code += subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
    if subprocess.call(['systemctl', 'is-active', '--quiet', 'decentrafly.service']) == 0:
        print("Restarting the service")
        exit_code += subprocess.call(['sudo', 'systemctl', 'restart', 'decentrafly.service'])
    else:
        exit_code += subprocess.call(['sudo', 'systemctl', 'enable', '--now', 'decentrafly.service'])
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")


def install(executable):
    if os.path.isfile('/usr/bin/decentrafly'):
        print("Found decentrafly on this machine, will upgrade ...")
    exit_code = 0
    if executable != '/usr/bin/decentrafly':
        exit_code += subprocess.call(['sudo', 'cp', executable, '/usr/bin/decentrafly'])
        exit_code += subprocess.call(['sudo', 'chmod', '777', '/usr/bin/decentrafly'])
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")
