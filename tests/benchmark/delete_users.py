#!/usr/bin/env python3

from uuid import uuid4

from tests.benchmark.init import *

User.objects.exclude_anonymous().exclude(username="akadmin").delete()
