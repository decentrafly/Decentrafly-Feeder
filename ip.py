from config import ec
import requests


def get_device_ips():
    device_ips_response = requests.request('GET', "https://" + ec('DCF_MAIN_DOMAIN') + '/api/devices/peer')
    return device_ips_response.json()
