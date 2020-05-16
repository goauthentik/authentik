#!/bin/bash -ex
/app/wait_for_db.py
"$@"
