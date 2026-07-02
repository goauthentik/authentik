import os
from pathlib import Path

BASE_DIR = Path(__file__).absolute().parent
STATICFILES_DIRS = [os.path.join(BASE_DIR, "testdata")]
