#!/bin/bash

version="$(curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE_103 2>/dev/null)" && \
rm chromedriver* 2> /dev/null 1>&2 ; \
wget "https://chromedriver.storage.googleapis.com/${version}/chromedriver_linux64.zip" 2> /dev/null 1>&2 && \
unzip chromedriver_linux64.zip 2> /dev/null 1>&2 && \
rm chromedriver_linux64.zip* 2> /dev/null 1>&2
