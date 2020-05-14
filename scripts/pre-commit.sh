#!/bin/bash -xe
isort -rc passbook
pyright
black passbook
scripts/coverage.sh
bandit -r passbook
pylint passbook
prospector
./manage.py generate_swagger -o swagger.yaml -f yaml
