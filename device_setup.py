from random import randrange
import json
import os
import requests
import subprocess
import tempfile
import uuid


systemd_service_file='''
[Unit]
Description=MQTT Sender Service
After=network.target

[Service]
WorkingDirectory=%h/.config/decentrafly
ExecStart=decentrafly sender
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


def register_new_device(config_dir):
    thing_name = client_id()
    config_content = {"DCF_CLIENT_ID": thing_name,
                      "DCF_MQTT_HOST": "almfwrqpajske-ats.iot.us-east-1.amazonaws.com",
                      "DCF_IOT_TOPIC": "beast/ingest/" + str(randrange(1, 100))}

    aws_root_ca = requests.request('GET', "https://www.amazontrust.com/repository/AmazonRootCA1.pem")
    response = requests.request('POST',
                                "https://decentrafly.org/api/device/register",
                                json={"thing_name": thing_name})
    data = response.json()
    write_to_file(os.path.expanduser("~/.config/decentrafly/cert.crt"), data['certs']['certificate'])
    write_to_file(os.path.expanduser("~/.config/decentrafly/private.key"), data['certs']['private_key'])
    write_to_file(os.path.expanduser("~/.config/decentrafly/ca.crt"), aws_root_ca.text)
    write_to_file(os.path.expanduser("~/.config/decentrafly/config.json"),
                                     json.dumps(config_content))


def prepare_directories(config_dir):
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)


def self_setup():
    config_dir = os.path.expanduser("~/.config/decentrafly")

    prepare_directories(config_dir)

    if not (os.path.isfile(os.path.expanduser("~/.config/decentrafly/ca.crt"))
            and os.path.isfile(os.path.expanduser("~/.config/decentrafly/cert.crt"))
            and os.path.isfile(os.path.expanduser("~/.config/decentrafly/private.key"))):
        register_new_device(config_dir)
        print("Setup done")
    else:
        print("Setup already done")


def enable_service(executable):
    try:
        if subprocess.call(['systemctl', '--user', 'status']) != 0:
            print("Error: I need systemd-user to enable the service.")
            exit(1)
    except Exception:
        print("systemctl not found")
        exit(1)

    print("Please provide the sudo password to install the service")
    exit_code = 0
    exit_code += subprocess.call(['sudo', 'echo'])
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(systemd_service_file)
        tmp.close()
        exit_code += subprocess.call(['sudo', 'mv', tmp.name, "/usr/lib/systemd/user/decentrafly.service"])
    if executable != '/usr/bin/decentrafly':
        exit_code += subprocess.call(['sudo', 'cp', executable, '/usr/bin/decentrafly'])
    exit_code += subprocess.call(['sudo', 'chmod', '777', '/usr/bin/decentrafly'])
    exit_code += subprocess.call(['systemctl', '--user', 'daemon-reload'])
    exit_code += subprocess.call(['systemctl', '--user', 'enable', '--now', 'decentrafly.service'])
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")
