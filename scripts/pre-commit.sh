#!/bin/bash -xe
isort -rc passbook
pyright
black passbook
./manage.py generate_swagger -o swagger.yaml -f yaml
scripts/coverage.sh
bandit -r passbook
pylint passbook
prospector
