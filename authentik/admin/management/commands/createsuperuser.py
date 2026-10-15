from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "ak createsuperuser should not be used. Instead, use ak create_admin_group"

    def handle(self, *args, **options):  # noqa: ANN001, D401
        raise RuntimeError(
            "ak createsuperuser should not be used. Instead, use ak create_admin_group"
        )
