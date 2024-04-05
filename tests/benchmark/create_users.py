#!/usr/bin/env python3

import sys
from uuid import uuid4

from tests.benchmark.init import *

while User.objects.count() < int(sys.argv[1]):
    User.objects.create(username=uuid4(), name=uuid4())
