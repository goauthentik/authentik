from django.core.management.base import BaseCommand

from guardian.utils import clean_orphan_obj_perms


class Command(BaseCommand):
    """A wrapper around `guardian.utils.clean_orphan_obj_perms`.

    Seeks and removes all object permissions entries pointing at non-existing targets.
    Returns the number of objects removed.

    Example:
        ```shell
        $ python manage.py clean_orphan_obj_perms
        Removed 11 object permission entries with no targets

        $ python manage.py clean_orphan_obj_perms --batch-size 100 --max-batches 5
        Removed 500 object permission entries with no targets
        ```
    """

    help = "Removes object permissions with not existing targets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            help="Number of objects to process per batch. If not specified, batch size is infinite",
        )
        parser.add_argument(
            "--max-batches",
            type=int,
            help="Maximum number of batches to process. Use with --batch-size.",
        )
        parser.add_argument(
            "--max-duration-secs",
            type=int,
            help="Maximum duration in seconds for the cleanup operation.",
        )
        parser.add_argument(
            "--skip-batches",
            type=int,
            default=0,
            help="Number of batches to skip before starting cleanup. Use with --batch-size.",
        )

    def handle(self, **options):
        kwargs = {}

        if options["batch_size"] is not None:
            kwargs["batch_size"] = options["batch_size"]

        if options["max_batches"] is not None:
            kwargs["max_batches"] = options["max_batches"]

        if options["max_duration_secs"] is not None:
            kwargs["max_duration_secs"] = options["max_duration_secs"]

        if options["skip_batches"] > 0:
            kwargs["skip_batches"] = options["skip_batches"]

        removed = clean_orphan_obj_perms(**kwargs)

        if options["verbosity"] > 0:
            self.stdout.write(f"Removed {removed} object permission entries with no targets")
