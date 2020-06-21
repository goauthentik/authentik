#!/bin/bash -x
sudo apt update
# Setup python
sudo apt install -y python3.8 python3-pip apt-transport-https ca-certificates curl gnupg-agent software-properties-common
# Setup nodejs
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g yarn
# Setup docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -a -G docker ubuntu
sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo pip3 install pipenv

cd e2e
sudo docker-compose up -d
cd ..
pipenv sync --dev
pipenv shell
