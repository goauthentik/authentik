#!/bin/bash -xe
docker-compose -f scripts/ci.docker-compose.yml up -d

sudo apt update
sudo apt install -y libxmlsec1-dev pkg-config
python3 -m pip install -U wheel poetry
poetry env use python3.10
if [[ "$INSTALL" != "true" ]]; then
    poetry install
fi
poetry run python -m scripts.generate_ci_config
npm install -g pyright@1.1.136
