#!/usr/bin/env bash
set -e
# set -x # Uncomment to Debug

cd "$(dirname "$0")"
if ! test -e venv; then
  echo "Creating python venv for macproxy"
  python3 -m venv venv
  echo "Activating venv"
  source venv/bin/activate
  echo "Installing requirements.txt"
  pip install wheel
  pip install -r requirements.txt
  git rev-parse HEAD > current
fi

source venv/bin/activate

# Detect if someone updates - we need to re-run pip install.
if ! test -e current; then
  git rev-parse > current
else
  if [ "$(cat current)" != "$(git rev-parse HEAD)" ]; then
      echo "New version detected, updating requirements.txt"
      pip install -r requirements.txt
      git rev-parse HEAD > current
  fi
fi

echo "Starting macproxy..."
python3 proxy.py
