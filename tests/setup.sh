#!/bin/bash -x
# Setup docker & compose
# curl -fsSL https://get.docker.com | bash
sudo usermod -a -G docker ubuntu
sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# Setup nodejs
curl -sL https://deb.nodesource.com/setup_15.x | sudo -E bash -
sudo apt-get install -y nodejs
# Setup k3d
curl -s https://raw.githubusercontent.com/rancher/k3d/main/install.sh | bash
# Setup python
sudo apt install -y python3.9 python3-pip libxmlsec1-dev pkg-config
# Setup docker
sudo pip3 install pipenv

cd tests/e2e
sudo docker-compose up -d
cd ../..
pipenv sync --dev
