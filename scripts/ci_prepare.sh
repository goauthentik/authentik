#!/bin/bash -xe
docker-compose -f scripts/ci.docker-compose.yml up -d

sudo apt update
sudo apt install -y libxmlsec1-dev pkg-config
sudo pip install -U wheel poetry
if [[ "$INSTALL" != "true" ]]; then
    poetry install
fi
poetry run python -m scripts.generate_ci_config
npm install -g pyright@1.1.136
