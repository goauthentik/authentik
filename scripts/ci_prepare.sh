#!/bin/bash
docker-compose -f scripts/ci.docker-compose.yml up -d
sudo apt update
sudo apt install -y libxmlsec1-dev pkg-config
sudo pip install -U wheel pipenv
pipenv install --dev
pipenv run python -m scripts.generate_ci_config
