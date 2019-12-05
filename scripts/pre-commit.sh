#!/bin/bash -xe
isort
pylint passbook
prospector
scripts/coverage.sh
