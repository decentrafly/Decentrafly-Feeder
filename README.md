# MQTT

BEAST data -> python sender -> MQTT -> python receiver -> TCP stream -> readsb

## Table of Contents

- [Installation](#installation)
- [Checking Connection](#checking-connection)
- [Online Confirmation](#online-confirmation)
- [Log Files](#log-files)
- [Getting Help](#getting-help)
- [Appendix](#appendix)

## Installation

To install Decentrafly's MQTT feeder, simply run the following one-line command in your terminal:

<pre>
curl -L https://raw.githubusercontent.com/decentrafly/MQTT/main/install.sh | bash
</pre>

## Checking-connection

After installing the software, you can check if the service is working by running the following terminal command:

<pre>
sudo systemctl status decentrafly
</pre>

## Online-confirmation

Confirm the MQTT status online at:

https://decentrafly.org/checkip

## Log-Files

To check the log files, use the following command:

<pre>
sudo journalctl -fu decentrafly
</pre>

## Getting-Help

if you encounter any issues or need help with <Project Name>, please share your log files in our Discord community:

Join our Discord server: 

https://discord.gg/wH2B7Anz


Navigate to the #Support channel.
Upload your log files and describe the issue you're experiencing.

## Appendix

Installation reads configuration file to set attributes for feeding at:

<pre>
/boot/adsb-config.txt
</pre>



Configuration can be adjusted at:

<pre>
/etc/decentrafly/config.json
</pre>

- DCF_CLIENT_ID: (System provided client ID that identifies this device)
- DCF_IOT_TOPIC: (System provided topic to stream data to)
- DCF_LOG_INTERVAL: seconds (integer) between log messages showing stats (default: "20")
- DCF_MAX_INTERVAL: max seconds (float) to buffer ADSB data before sending it (recommended > 0.2, default "1.0")
- DCF_READSB_HOST: readsb host to connect to (default: "localhost")
- DCF_READSB_PORT": beast out port of the readsb (default: "30005")
- DCF_TRIGGER_SIZE": max bytes to buffer ADSB data before sending it out (default: "50000")
