#!/bin/bash -xe
coverage run --concurrency=multiprocessing manage.py test passbook --failfast
coverage combine
coverage html
coverage report
