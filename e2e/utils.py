"""passbook e2e testing utilities"""

from glob import glob
from inspect import getmembers, isfunction
from importlib.util import spec_from_file_location, module_from_spec
from django.apps import apps
from django.db import connection, transaction
from django.db.utils import IntegrityError

def apply_default_data():
    """apply objects created by migrations after tables have been truncated"""
    # Find all migration files
    # load all functions
    migration_files = glob("**/migrations/*.py", recursive=True)
    matches = []
    for migration in migration_files:
        with open(migration, 'r+') as migration_file:
            # Check if they have a `RunPython`
            if "RunPython" in migration_file.read():
                matches.append(migration)

    with connection.schema_editor() as schema_editor:
        for match in matches:
            # Load module from file path
            spec = spec_from_file_location("", match)
            migration_module = module_from_spec(spec)
            # pyright: reportGeneralTypeIssues=false
            spec.loader.exec_module(migration_module)
            # Call all functions from module
            for _, func in getmembers(migration_module, isfunction):
                with transaction.atomic():
                    try:
                        func(apps, schema_editor)
                    except IntegrityError:
                        pass
