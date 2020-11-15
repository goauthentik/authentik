#!/bin/bash -xe
wget -q -O - https://raw.githubusercontent.com/rancher/k3d/main/install.sh | bash

VERSION=3.9.0

wget https://www.python.org/ftp/python/$VERSION/Python-$VERSION.tgz
tar xvzf Python-$VERSION.tgz
cd Python-$VERSION/

./configure --prefix=$HOME/_work/_tool/Python/$VERSION/x64/ --enable-optimizations --with-ensurepip=install
make -j 8
sudo make altinstall
touch $HOME/_work/_tool/Python/$VERSION/x64.complete

ln -s $HOME/_work/_tool/Python/3.9.5/x64 $HOME/_work/_tool/Python/3/x64
ln -s $HOME/_work/_tool/Python/3.9.5/x64 $HOME/_work/_tool/Python/3.9/x64
