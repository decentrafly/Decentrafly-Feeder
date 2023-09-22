#!/bin/bash

set -euo pipefail

function help_package_install() {
    cat <<HERE
On Debian-based systems

Missing  Install command
-------  ---------------
curl     sudo apt-get install curl
env      sudo apt-get install coreutils
mktemp   sudo apt-get install coreutils
pip3     sudo apt-get install python3-pip
python3  sudo apt-get install python3

HERE
}

function check_dependency() {
    which "$1" &> /dev/null || {
        echo "Missing dependency: $1; Please install it on your system."
        echo
        help_package_install
        exit 1
    }
}

# Pre-Flight Checks
check_dependency curl
check_dependency env
check_dependency mktemp
check_dependency pip3
check_dependency python3

cd "$(mktemp -d)"


curl -L 'https://github.com/decentrafly/Decentrafly-Feeder/releases/download/v2023-09-22/decentrafly' > decentrafly
echo "Checking file integrity"
echo '0ba656b9a3fc7a3aa557fc28bdd4d482c0b0fe94  decentrafly' | sha1sum --check


chmod 777 decentrafly

echo "Installing dependencies ..."
sudo pip3 install awscrt==0.16.13 awsiot==0.1.3 awsiotsdk==1.12.6 boto3==1.26.87 requests==2.28.2 asyncio==3.4.3

./decentrafly setup < /dev/tty
./decentrafly install
./decentrafly enable
