"""Migration helpers"""
from typing import Iterable

from django.apps.registry import Apps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def fallback_names(app: str, model: str, field: str):
    """Factory function that checks all instances of `app`.`model` instance's `field`
    to prevent any duplicates"""

    def migrator(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
        db_alias = schema_editor.connection.alias

        klass = apps.get_model(app, model)
        seen_names = []
        for obj in klass.objects.using(db_alias).all():
            value = getattr(obj, field)
            if value not in seen_names:
                seen_names.append(value)
                continue
            separator = "_"
            suffix_index = 2
            while (
                klass.objects.using(db_alias)
                .filter(**{field: f"{value}{separator}{suffix_index}"})
                .exists()
            ):
                suffix_index += 1
            new_value = f"{value}{separator}{suffix_index}"
            setattr(obj, field, new_value)
            obj.save()

    return migrator


def progress_bar(iterable: Iterable):
    """Call in a loop to create terminal progress bar
    https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console"""

    prefix = "Writing: "
    suffix = " finished"
    decimals = 1
    length = 100
    fill = "█"
    print_end = "\r"

    total = len(iterable)
    if total < 1:
        return

    def print_progress_bar(iteration):
        """Progress Bar Printing Function"""
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + "-" * (length - filled_length)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)

    # Initial Call
    print_progress_bar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        print_progress_bar(i + 1)
    # Print New Line on Complete
    print()
