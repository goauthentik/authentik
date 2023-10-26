# Helper script to generate an NPM version
from time import time
from authentik import __version__

# Generate a unique version based on the current version and a timestamp
npm_version = f"{__version__}-{int(time())}"

print(npm_version)
