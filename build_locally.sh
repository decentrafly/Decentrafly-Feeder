#!/bin/bash
rm -f decentrafly decentrafly.zip
echo "$(date +'%Y%m%d%H%M%S')-dev" > version.txt
zip -r decentrafly *.py requirements.txt version.txt&& cat bootstrap decentrafly.zip > decentrafly
