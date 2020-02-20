#!/bin/bash -xe
isort -rc passbook
black passbook
scripts/coverage.sh
pylint passbook
prospector
