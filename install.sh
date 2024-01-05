#!/bin/bash

set -euo pipefail

if [[ -z "${2+x}" ]]; then
    echo "Usage: install.sh <invite-id> <invite-signature>"
    exit 1
fi

download_path='https://github.com/decentrafly/Decentrafly-Feeder/releases/download/v2024-01-05_2/decentrafly'
checksum='cb22232c6c0018c76068757a855d84efb2182706  decentrafly'
invite_id="$1"
invite_sig="$2"

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

function download_checksummed_binary() {
    local target_path="$1"
    local source_url="$2"
    local sha1_checksum="$3"

    local tmp_path="$(mktemp)"

    curl -L "$source_url" > "$tmp_path"
    echo "Checking file integrity for $source_url"
    echo "$sha1_checksum  $tmp_path" | sha1sum --check || { echo "Verify failed"; exit 1; }
    pwd
    cp "$tmp_path" "$target_path"
}

# Pre-Flight Checks
check_dependency curl
check_dependency env
check_dependency mktemp
check_dependency pip3
check_dependency python3

cd "$(mktemp -d)"

echo "Installing dependencies ..."
sudo pip3 install awscrt==0.16.13 awsiot==0.1.3 awsiotsdk==1.12.6 boto3==1.26.87 requests==2.28.2 asyncio==3.4.3

download_checksummed_binary ./decentrafly "$download_path" "$checksum"
chmod 777 ./decentrafly

./decentrafly setup "$invite_id" "$invite_sig" < /dev/tty
./decentrafly install
./decentrafly enable
