#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/pi-weather-station"
VENV_DIR="$APP_DIR/.venv"

apt-get update
apt-get install -y \
  python3 python3-venv python3-pip python3-dev \
  build-essential \
  i2c-tools spi-tools gpiod \
  python3-gpiozero python3-smbus python3-smbus2 \
  python3-serial \
  libgpiod2 pigpio python3-pigpio

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip wheel setuptools
"$VENV_DIR/bin/pip" install --upgrade .