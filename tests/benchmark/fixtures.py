#!/usr/bin/env python3

import sys
from os import environ
from uuid import uuid4

import django

environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
environ.setdefault("AUTHENTIK_BOOTSTRAP_PASSWORD", "akadmin")
environ.setdefault("AUTHENTIK_BOOTSTRAP_TOKEN", "akadmin")
environ.setdefault("AUTHENTIK_BOOTSTRAP_EMAIL", "akadmin@authentik.test")
django.setup()

from django.conf import settings

from authentik.core.models import Group, User
from authentik.tenants.models import Domain, Tenant

settings.CELERY["task_always_eager"] = True


def user_list():
    # Number of users, groups per user, parents per groups
    tenants = [
        (10, 0, 0),
        (100, 0, 0),
        (1000, 0, 0),
        (10000, 0, 0),
        (10, 20, 0),
        (100, 20, 0),
        (1000, 20, 0),
        (10000, 20, 0),
        (10, 20, 10),
        (100, 20, 10),
        (1000, 20, 10),
        (10000, 20, 10),
    ]

    for tenant in tenants:
        user_count = tenant[0]
        groups_per_user = tenant[1]
        parents_per_group = tenant[2]
        tenant_name = f"user-list-{user_count}-{groups_per_user}-{parents_per_group}"

        t = Tenant.objects.create(schema_name=f"t_{tenant_name.replace('-', '_')}", name=uuid4())
        Domain.objects.create(tenant=t, domain=f"{tenant_name}.localhost")

        with t:
            for _ in range(user_count):
                User.objects.create(username=uuid4(), name=uuid4())
            for user in User.objects.exclude_anonymous().exclude(username="akadmin"):
                for _ in range(groups_per_user):
                    user.ak_groups.add(Group.objects.create(name=uuid4()))
            for group in Group.objects.exclude(name="authentik Admins"):
                for _ in range(parents_per_group):
                    new_group = Group.objects.create(name=uuid4())
                    group.parent = new_group
                    group.save()
                    group = new_group


def delete():
    Tenant.objects.exclude(schema_name="public").delete()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        action = "create"
    else:
        action = sys.argv[1]

    match action:
        case "create":
            user_list()
        case "delete":
            delete()
        case _:
            print("Unknown action. Should be create or delete")
            exit(1)
