#!/bin/bash -xe
isort -rc .
pyright
black .
./manage.py generate_swagger -o swagger.yaml -f yaml
scripts/coverage.sh
bandit -r .
pylint passbook
prospector
