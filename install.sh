#!/bin/bash

set -euo pipefail

function help_package_install() {
    cat <<HERE
On Debian-based systems

Missing  Install command
-------  ---------------
curl     sudo apt-get install curl
pip3     sudo apt-get install python3-pip
python3  sudo apt-get install python3
unzip    sudo apt-get install unzip

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
check_dependency pip3
check_dependency python3
check_dependency unzip


# curl ... > decentrafly
echo "Checking file integrity"
echo 'f12db7015d1e7f679c5830231c296e9c3ecc3318  decentrafly' | sha1sum --check

chmod 777 decentrafly

echo "Installing dependencies ..."
pip3 install $(unzip -p decentrafly requirements.txt)

./decentrafly setup
./decentrafly enable
