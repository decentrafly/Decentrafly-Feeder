from random import randrange
import json
import os
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


def register_new_device(temporary_dir):
    thing_name = client_id()
    config_content = {"DCF_CLIENT_ID": thing_name,
                      "DCF_MQTT_HOST": "almfwrqpajske-ats.iot.us-east-1.amazonaws.com",
                      "DCF_IOT_TOPIC": "beast/ingest/" + str(randrange(1, 100))}

    aws_root_ca = requests.request('GET', "https://www.amazontrust.com/repository/AmazonRootCA1.pem")
    response = requests.request('POST',
                                "https://decentrafly.org/api/device/register",
                                json={"thing_name": thing_name})
    data = response.json()
    write_to_file(os.path.join(temporary_dir, "cert.crt"), data['certs']['certificate'])
    write_to_file(os.path.join(temporary_dir, "private.key"), data['certs']['private_key'])
    write_to_file(os.path.join(temporary_dir, "ca.crt"), aws_root_ca.text)
    write_to_file(os.path.join(temporary_dir, "config.json"),
                  json.dumps(config_content, indent=2))


def self_setup():
    if not (os.path.isfile(os.path.expanduser("/etc/decentrafly/ca.crt"))
            and os.path.isfile(os.path.expanduser("/etc/decentrafly/cert.crt"))
            and os.path.isfile(os.path.expanduser("/etc/decentrafly/private.key"))):
        print("Please provide the sudo password to write config files to /etc/decentrafly")
        exit_code = 0
        exit_code += subprocess.call(['sudo', 'echo'])
        with tempfile.TemporaryDirectory() as tmpdirname:
            register_new_device(tmpdirname)
            exit_code += subprocess.call(['sudo', 'cp', '-r', tmpdirname, "/etc/decentrafly"])
            exit_code += subprocess.call(['sudo', 'chmod', '755', tmpdirname, "/etc/decentrafly"])
        if exit_code == 0:
            print("Setup done")
        else:
            print("Setup failed")
    else:
        print("Setup already done")


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
    exit_code += subprocess.call(['sudo', 'systemctl', 'enable', '--now', 'decentrafly.service'])
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")


def install(executable):
    exit_code = 0
    if executable != '/usr/bin/decentrafly':
        exit_code += subprocess.call(['sudo', 'cp', executable, '/usr/bin/decentrafly'])
        exit_code += subprocess.call(['sudo', 'chmod', '777', '/usr/bin/decentrafly'])
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")
