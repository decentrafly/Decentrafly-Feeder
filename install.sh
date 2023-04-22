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
check_dependency python3

cd "$(mktemp -d)"

curl -L 'https://github.com/decentrafly/MQTT/releases/download/v2023-04-22/decentrafly' > decentrafly
echo "Checking file integrity"
echo 'c43e77df6944b47e15d26695f61091e52efb8626  decentrafly' | sha1sum --check

chmod 777 decentrafly

./decentrafly setup
./decentrafly install
./decentrafly enable
