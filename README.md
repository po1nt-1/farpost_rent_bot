# farpost_rent_bot

Telegram notifications about new ads on Farpost.ru

## Dependencies

* python 3.9
* google-chrome and chromedriver v110

## Installation

### Install google chrome and google chrome driver

```bash
./driver_install.sh
```

### Setup virtual environment and install python-requirements

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Prepare the configuration file
```bash
cp -a config.yaml.example config.yaml
vim config.yaml
```

### Run it
```bash
python3 main.py
```

## To reset all the data
```bash
rm -rf driver_profile/ ads.log
```
