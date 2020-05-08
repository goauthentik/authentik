#!/bin/bash -xe
coverage run --concurrency=multiprocessing manage.py test --failfast
coverage combine
coverage html
coverage report
