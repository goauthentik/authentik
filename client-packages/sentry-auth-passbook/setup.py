#!/usr/bin/env python
"""
sentry-auth-passbook
==================

:copyright: (c) 2016 Functional Software, Inc
"""
from setuptools import find_packages, setup

install_requires = [
    'sentry>=7.0.0',
]

tests_require = [
    'mock',
    'flake8>=2.0,<2.1',
]

setup(
    name='sentry-auth-passbook',
    version='0.1.38-beta',
    author='BeryJu.org',
    author_email='support@beryju.org',
    url='https://passbook.beryju.org',
    description='passbook authentication provider for Sentry',
    long_description=__doc__,
    license='MIT',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'auth_passbook = sentry_auth_passbook',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
