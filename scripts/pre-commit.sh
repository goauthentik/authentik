#!/bin/bash -xe
isort -rc passbook
black passbook
scripts/coverage.sh
bandit -r passbook
pylint passbook
prospector
