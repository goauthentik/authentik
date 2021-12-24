#!/bin/bash -xe
docker-compose -f scripts/ci.docker-compose.yml up -d

sudo apt update
sudo apt install -y libxmlsec1-dev pkg-config
python3 -m pip install -U wheel poetry
if [[ "$INSTALL" != "true" ]]; then
    python3 -m poetry install
fi
python3 -m poetry run pip install backports.zoneinfo
python3 -m poetry run python -m scripts.generate_ci_config
npm install -g pyright@1.1.136
