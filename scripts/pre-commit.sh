#!/bin/bash -xe
scripts/coverage.sh
isort
pylint passbook
prospector
