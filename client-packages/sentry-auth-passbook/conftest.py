from __future__ import absolute_import

# Run tests against sqlite for simplicity
import os
import os.path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

os.environ.setdefault('DB', 'sqlite')

pytest_plugins = [
    'sentry.utils.pytest'
]
