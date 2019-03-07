#!/bin/bash

# Check if this file is a symlink, if so, read real base dir
BASE_DIR=$(dirname $(readlink -f ${BASH_SOURCE[0]}))

cd $BASE_DIR
PYTHONPATH="${BASE_DIR}/vendor/" python3 manage.py $@
