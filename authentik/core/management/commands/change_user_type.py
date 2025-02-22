"""Change user type"""

from authentik.core.models import User, UserTypes
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Change user type"""

    def add_arguments(self, parser):
        parser.add_argument("--type", type=str, required=True)
        parser.add_argument("--all", action="store_true", default=False)
        parser.add_argument("usernames", nargs="*", type=str)

    def handle_per_tenant(self, **options):
        print(options)
        new_type = UserTypes(options["type"])
        qs = (
            User.objects.exclude_anonymous()
            .exclude(type=UserTypes.SERVICE_ACCOUNT)
            .exclude(type=UserTypes.INTERNAL_SERVICE_ACCOUNT)
        )
        if options["usernames"] and options["all"]:
            self.stderr.write("--all and usernames specified, only one can be specified")
            return
        if not options["usernames"] and not options["all"]:
            self.stderr.write("--all or usernames must be specified")
            return
        if options["usernames"] and not options["all"]:
            qs = qs.filter(username__in=options["usernames"])
        updated = qs.update(type=new_type)
        self.stdout.write(f"Updated {updated} users.")
