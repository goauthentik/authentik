"""Helper script to generate an NPM Version"""

from time import time

from authentik import __version__

print(f"{__version__}-{int(time())}")
