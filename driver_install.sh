#!/bin/bash

set -e # -x

if command -v yum >/dev/null; then
    sudo yum install -qq -y 'https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm'
elif command -v apt >/dev/null; then
    wget -q 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb' -O 'google-chrome-stable_current_amd64.deb' && \
    sudo apt install -qq -y './google-chrome-stable_current_amd64.deb' && \
    rm 'google-chrome-stable_current_amd64.deb'
else
  echo "You need to install google-chrome"; exit -1
fi

google-chrome --version

version="$(google-chrome --version | cut -d' ' -f3 | cut -d'.' -f1)" && \
version="$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${version})" && \

wget -q "https://chromedriver.storage.googleapis.com/${version}/chromedriver_linux64.zip" -O chromedriver_linux64.zip && \
unzip -q -o chromedriver_linux64.zip chromedriver && \
rm -f chromedriver_linux64.zip* && \
./chromedriver --version | cut -d' ' -f1,2

