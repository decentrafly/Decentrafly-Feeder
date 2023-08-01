from random import randrange
import config
import json
import os
import re
import requests
import subprocess
import tempfile


main_systemd_service_file = '''[Unit]
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

mlat_forwarder_systemd_service_file = '''[Unit]
Description=MLAT mTLS Forwarder Service
After=network.target

[Service]
ExecStart=/usr/bin/decentrafly mlat-forwarder
Environment="PYTHONUNBUFFERED=1"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''

mlat_client_system_service_file = '''[Unit]
Description=decentrafly-mlat-client
Wants=network.target
After=network.target
After=decentrafly-mlat-forwarder.service

[Service]
EnvironmentFile=/boot/adsb-config.txt
Environment=INPUT_TYPE=dump1090 "INPUT=127.0.0.1:30005" "MLATSERVER=localhost:41090"
ExecStart=/usr/local/bin/mlat.sh
Type=simple
Restart=on-failure
RestartSec=30
RestartPreventExitStatus=64
SyslogIdentifier=decentrafly-mlat-client

[Install]
WantedBy=default.target
'''

decentrafly_agent_systemd_service_file = '''[Unit]
Description=Decentrafly Agent Service
After=network.target

[Service]
ExecStart=/usr/bin/decentrafly agent
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


def check_setup_dependencies():
    try:
        if subprocess.call(['sudo', 'which', 'systemctl']) != 0:
            print("Error: I need systemd to enable the service.")
            exit(1)
    except Exception:
        print("systemctl not found")
        exit(1)


def register_new_device(temporary_dir, device_attributes):
    aws_root_ca = requests.request('GET', "https://www.amazontrust.com/repository/AmazonRootCA1.pem")
    print("Generating a device ID and new certificates ...")
    response = requests.request('POST',
                                "https://decentrafly.org/api/device/register/v2",
                                json={"attributes": device_attributes})
    data = response.json()
    write_to_file(os.path.join(temporary_dir, "cert.crt"), data['mqtt']['certs']['certificate'])
    write_to_file(os.path.join(temporary_dir, "private.key"), data['mqtt']['certs']['private_key'])
    write_to_file(os.path.join(temporary_dir, "ca.crt"), aws_root_ca.text)
    write_to_file(os.path.join(temporary_dir, "mtls-cert.crt"), data['mtls']['certificate'])
    write_to_file(os.path.join(temporary_dir, "mtls-private.key"), data['mtls']['private_key'])
    write_to_file(os.path.join(temporary_dir, "mtls-ca.crt"), data['mtls']['ca'])

    config_content = {"DCF_FEEDER_ID": data['feeder_id'],
                      "DCF_CLIENT_ID": data['mqtt']['thing']['name'],
                      "DCF_MQTT_HOST": "almfwrqpajske-ats.iot.us-east-1.amazonaws.com",
                      "DCF_IOT_TOPIC": "beast/ingest/" + str(randrange(1, 100))}
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
        print("We kindly ask to provide this information, but you can leave it empty if you prefer.")
        print("The information can help you manage your devices later.\n")

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

        print("\n\nI might ask for the sudo password to write config files to /etc/decentrafly")
        exit_code = 0
        exit_code += subprocess.call(['sudo', 'echo'])
        print("OK")
        with tempfile.TemporaryDirectory() as tmpdirname:
            print("Registering a new device with decentrafly, this might take up to a minute ...")
            register_new_device(tmpdirname, device_attributes)
            exit_code += subprocess.call(['sudo', 'cp', '-r', tmpdirname, "/etc/decentrafly"])
            exit_code += subprocess.call(['sudo', 'chmod', '755', tmpdirname, "/etc/decentrafly"])
        if exit_code == 0:
            print("Setup done")
        else:
            print("Setup failed")
    else:
        print("Setup already done, I won't touch config or certificates")


def update_iot_device():
    # We load the config directly from file, because this happens in
    # the same run as the self_setup. So config.effective_config is
    # not up to date as currently it's only loaded on startup
    up_to_date_config = config.load_config()
    if up_to_date_config['DCF_CLIENT_ID']:
        print("Updating device configuration on decentrafly backend ...")
        requests.request(
            'POST',
            "https://decentrafly.org/api/device/update",
            json={"thing_name": up_to_date_config['DCF_CLIENT_ID']}
        )
    else:
        print("Update iot device failed.")


def ensure_running_systemd_service(service):
    if subprocess.call(['systemctl', 'is-active', '--quiet', service]) == 0:
        print("Restarting the service {}".format(service))
        return subprocess.call(['sudo', 'systemctl', 'restart', service])
    else:
        return subprocess.call(['sudo', 'systemctl', 'enable', '--now', service])


def unpack_file(path, content):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(content)
        tmp.close()
        return subprocess.call(['sudo', 'mv', tmp.name, path])


def download_file(path, url, chmod=None):
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        print("Downloading {} ...".format(url))
        resp = requests.get(url, allow_redirects=True)
        tmp.write(resp.content)
        tmp.close()
        if chmod:
            exit_code = subprocess.call(['sudo', 'chmod', chmod, tmp.name])
        return exit_code + subprocess.call(['sudo', 'mv', tmp.name, path])


def enable_services(executable):
    exit_code = 0

    check_setup_dependencies()
    print("Please provide the sudo password to install the service")
    exit_code += subprocess.call(['sudo', 'echo'])

    # Install the main forwarder service (MQTT)
    exit_code += unpack_file("/usr/lib/systemd/system/decentrafly.service", main_systemd_service_file)
    exit_code += unpack_file("/usr/lib/systemd/system/decentrafly-mlat-forwarder.service", mlat_forwarder_systemd_service_file)
    exit_code += unpack_file("/usr/lib/systemd/system/decentrafly-mlat-client.service", mlat_client_system_service_file)
    exit_code += subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
    exit_code += ensure_running_systemd_service('decentrafly.service')
    exit_code += ensure_running_systemd_service('decentrafly-mlat-forwarder.service')
    exit_code += ensure_running_systemd_service('decentrafly-mlat-client.service')

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


def install_agent():
    localproxy_url = "https://decentrack-prod-binaries.s3.amazonaws.com/tools/arm32/localproxy"
    exit_code = 0
    exit_code += download_file("/usr/bin/localproxy", localproxy_url, "777")
    exit_code += unpack_file("/usr/lib/systemd/system/decentrafly-agent.service",
                             decentrafly_agent_systemd_service_file)
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")


def setup_agent():
    check_setup_dependencies()
    if not (os.path.isfile("/usr/bin/localproxy")
            and os.path.isfile("/usr/lib/systemd/system/decentrafly-agent.service")):
        install_agent()
    exit_code = 0
    exit_code += config.persist_config_entry("DCF_REMOTE_ACCESS", "True")
    exit_code += ensure_running_systemd_service("decentrafly-agent.service")
    if exit_code == 0:
        print("Done")
    else:
        print("Failed")


def upgrade(executable):
    url = "https://github.com/decentrafly/MQTT-Feeder/releases/latest/download/decentrafly"
    if download_file(executable, url) == 0:
        subprocess.call(['sudo', 'chmod', '777', executable])
        print("Done")
    else:
        print("Failed")
