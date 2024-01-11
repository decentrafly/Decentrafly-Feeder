# Decentrafly Installation Instructions

Follow these steps to install Decentrafly's Feeder onto your Raspberry Pi Device.

## Table of Contents

- [Installation](#installation)
- [Checking Connection](#checking-connection)
- [Online Confirmation](#online-confirmation)
- [Create an Account on Decentrafly](#account-signup)
- [Claim Feeder to Join ADS-B Leaderboard](#account-signup)
- [Log Files](#log-files)
- [Getting Help](#getting-help)
- [Appendix](#appendix)

## Installation

To install Decentrafly's feeder, simply run the following one-line command in your terminal:

<pre>
curl -L https://raw.githubusercontent.com/decentrafly/Decentrafly-Feeder/main/install.sh | bash /dev/stdin <invite-id> <invite-signature>
</pre>

This installs the services:
- decentrafly-adsb-forwarder.service (Service to forward ADS-B Beast data to Decentrafly)
- decentrafly-mlat-client.service (Service to run MLAT locally and establish a secure mTLS connection between Client and Server)
- decentrafly-mlat-forwarder.service (Service to forward MLAT data over mTLS connection to Server)

## Checking-connection

After installing the software, you can check if the ADSB Forwarder service is working by running the following terminal command:

<pre>
sudo systemctl status decentrafly-adsb-forwarder
</pre>

## Online-confirmation

Confirm your device's status online at:

https://decentrafly.org/checkip

or 

Check the Tar1090 map at:

https://globe.decentrafly.org

## Account-Signup

To sign up for an account to join the ADS-B Leaderboard:

Navigate to:

https://ui.decentrafly.org/

- Click on "Signup" at the bottom
- Complete the form
- Confirm your email with the verification code
- Navigate to the "Devices" tab
- Select "Claim Device"

Your device will now be linked to your account for joining the ADS-B Leaderboard and receiving device health updates.

## Log-Files

To check the log files for the ADS-B Forwarder, use the following command:

<pre>
sudo journalctl -fu decentrafly-adsb-forwarder
</pre>

## Getting-Help

To access the help menu, run the following command:
<pre> decentrafly </pre> 


</br>


To update to the latest version, run the following command:

<pre> decentrafly upgrade </pre>




</br>

If you encounter any issues or need help with the Decentrafly service, please share your log files in our Discord community:

Join our Discord server: 

https://discord.gg/VmeAVHaH

Navigate to the #Support channel.

Upload your log files and describe the issue you're experiencing.



## Appendix

If you have not updated or installed pip3 follow these steps:

<pre>
sudo apt update
</pre>


<pre>
sudo apt upgrade
</pre>


<pre>
sudo apt install python3-pip
</pre>

<pre>
pip --version
</pre>

## Setup Remote Access (Optional)

The service: 
 - decentrafly-agent.service (Optional service to check device health and diagnostics)

Can be installed by running the optional installation:

<pre>decentrafly setup agent</pre>

This will enable remote access to the device for diagnostics, only recommended if you have already reached out on Discord for Support from Decentrafly.

## Configuration

Installation reads a configuration file to set attributes for feeding at:

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
