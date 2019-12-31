#!/bin/bash -xe
black passbook
scripts/coverage.sh
pylint passbook
prospector
