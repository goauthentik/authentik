#!/usr/bin/env python3
import random
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

from authentik.core.models import Application, Group, User
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.stages.authenticator_static.models import StaticToken
from authentik.tenants.models import Domain, Tenant

settings.CELERY["task_always_eager"] = True

host = environ.get("BENCH_HOST", "localhost")


def user_list():
    # Number of users, groups per user, parents per groups
    tenants = [
        (1000, 0, 0),
        (10000, 0, 0),
        (1000, 3, 0),
        (10000, 3, 0),
        (1000, 20, 0),
        (10000, 20, 0),
        (1000, 20, 3),
        (10000, 20, 3),
    ]

    for tenant in tenants:
        user_count = tenant[0]
        groups_per_user = tenant[1]
        parents_per_group = tenant[2]
        tenant_name = f"user-list-{user_count}-{groups_per_user}-{parents_per_group}"

        schema_name = f"t_{tenant_name.replace('-', '_')}"
        created = False
        t = Tenant.objects.filter(schema_name=schema_name).first()
        if not t:
            created = True
            t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
        Domain.objects.get_or_create(tenant=t, domain=f"{tenant_name}.{host}")
        if not created:
            continue

        with t:
            Group.objects.bulk_create([Group(name=uuid4()) for _ in range(groups_per_user * 5)])
            for group in Group.objects.exclude(name="authentik Admins"):
                for _ in range(parents_per_group):
                    new_group = Group.objects.create(name=uuid4())
                    group.parent = new_group
                    group.save()
                    group = new_group
            User.objects.bulk_create(
                [
                    User(
                        username=uuid4(),
                        name=uuid4(),
                    )
                    for _ in range(user_count)
                ]
            )
            if groups_per_user:
                for user in User.objects.exclude_anonymous().exclude(username="akadmin"):
                    user.ak_groups.set(
                        Group.objects.exclude(name="authentik Admins").order_by("?")[
                            :groups_per_user
                        ]
                    )


def group_list():
    # Number of groups, users per group, with_parent
    tenants = [
        (1000, 0, False),
        (10000, 0, False),
        (1000, 1000, False),
        (1000, 10000, False),
        (1000, 0, True),
        (10000, 0, True),
    ]

    for tenant in tenants:
        group_count = tenant[0]
        users_per_group = tenant[1]
        with_parent = tenant[2]
        tenant_name = f"group-list-{group_count}-{users_per_group}-{str(with_parent).lower()}"

        schema_name = f"t_{tenant_name.replace('-', '_')}"
        created = False
        t = Tenant.objects.filter(schema_name=schema_name).first()
        if not t:
            created = True
            t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
        Domain.objects.get_or_create(tenant=t, domain=f"{tenant_name}.{host}")
        if not created:
            continue

        with t:
            User.objects.bulk_create(
                [
                    User(
                        username=uuid4(),
                        name=uuid4(),
                    )
                    for _ in range(users_per_group * 5)
                ]
            )
            if with_parent:
                parents = Group.objects.bulk_create(
                    [Group(name=uuid4()) for _ in range(group_count)]
                )
            groups = Group.objects.bulk_create(
                [
                    Group(name=uuid4(), parent=(parents[i] if with_parent else None))
                    for i in range(group_count)
                ]
            )
            if users_per_group:
                for group in groups:
                    group.users.set(
                        User.objects.exclude_anonymous()
                        .exclude(username="akadmin")
                        .order_by("?")[:users_per_group]
                    )


def login():
    schema_name = f"t_login_no_mfa"
    created = False
    t = Tenant.objects.filter(schema_name=schema_name).first()
    if not t:
        created = True
        t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
    Domain.objects.get_or_create(tenant=t, domain=f"login-no-mfa.{host}")
    if created:
        with t:
            user = User(username="test", name=uuid4())
            user.set_password("verySecurePassword")
            user.save()

    schema_name = f"t_login_with_mfa"
    created = False
    t = Tenant.objects.filter(schema_name=schema_name).first()
    if not t:
        created = True
        t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
    Domain.objects.get_or_create(tenant=t, domain=f"login-with-mfa.{host}")
    if created:
        with t:
            user = User(username="test", name=uuid4())
            user.set_password("verySecurePassword")
            user.save()
            device = user.staticdevice_set.create()
            # Multiple token with same token for all the iterations in the test
            device.token_set.bulk_create(
                [StaticToken(device=device, token=f"staticToken") for _ in range(1_000_000)]
            )


def provider_oauth2():
    tenants = [
        # Number of user policies, group policies, expression policies
        (2, 50, 2),
        (0, 0, 0),
        (10, 0, 0),
        (100, 0, 0),
        (0, 10, 0),
        (0, 100, 0),
        (0, 0, 10),
        (0, 0, 100),
        (10, 10, 10),
        (100, 100, 100),
    ]

    for tenant in tenants:
        user_policies_count = tenant[0]
        group_policies_count = tenant[1]
        expression_policies_count = tenant[2]
        tenant_name = f"provider-oauth2-{user_policies_count}-{group_policies_count}-{expression_policies_count}"

        schema_name = f"t_{tenant_name.replace('-', '_')}"
        created = False
        t = Tenant.objects.filter(schema_name=schema_name).first()
        if not t:
            created = True
            t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
        Domain.objects.get_or_create(tenant=t, domain=f"{tenant_name}.{host}")
        if not created:
            continue

        with t:
            user = User(username="test", name=uuid4())
            user.set_password("verySecurePassword")
            user.save()

            provider = OAuth2Provider.objects.create(
                name="test",
                authorization_flow=Flow.objects.get(
                    slug="default-provider-authorization-implicit-consent"
                ),
                signing_key=CertificateKeyPair.objects.get(
                    name="authentik Self-signed Certificate"
                ),
                redirect_uris="http://test.localhost",
                client_id="123456",
                client_secret="123456",
            )
            application = Application.objects.create(slug="test", name="test", provider=provider)

            User.objects.bulk_create(
                [
                    User(
                        username=uuid4(),
                        name=uuid4(),
                    )
                    for _ in range(user_policies_count)
                ]
            )
            PolicyBinding.objects.bulk_create(
                [
                    PolicyBinding(
                        user=user,
                        target=application,
                        order=random.randint(1, 1_000_000),
                    )
                    for user in User.objects.exclude(username="akadmin").exclude_anonymous()
                ]
            )

            Group.objects.bulk_create([Group(name=uuid4()) for _ in range(group_policies_count)])
            PolicyBinding.objects.bulk_create(
                [
                    PolicyBinding(
                        group=group,
                        target=application,
                        order=random.randint(1, 1_000_000),
                    )
                    for group in Group.objects.exclude(name="authentik Admins")
                ]
            )
            user.ak_groups.set(Group.objects.exclude(name="authentik Admins").order_by("?")[:1])

            [
                ExpressionPolicy(
                    name=f"test-{uuid4()}",
                    expression="return True",
                ).save()
                for _ in range(expression_policies_count)
            ]
            PolicyBinding.objects.bulk_create(
                [
                    PolicyBinding(
                        policy=policy,
                        target=application,
                        order=random.randint(1, 1_000_000),
                    )
                    for policy in ExpressionPolicy.objects.filter(name__startswith="test-")
                ]
            )


def event_list():
    tenants = [
        # Number of events
        1_000,
        10_000,
        100_000,
        1_000_000,
    ]

    for tenant in tenants:
        event_count = tenant
        tenant_name = f"event-list-{event_count}"

        schema_name = f"t_{tenant_name.replace('-', '_')}"
        created = False
        t = Tenant.objects.filter(schema_name=schema_name).first()
        if not t:
            created = True
            t = Tenant.objects.create(schema_name=schema_name, name=uuid4())
        Domain.objects.get_or_create(tenant=t, domain=f"{tenant_name}.{host}")
        if not created:
            continue

        with t:
            Event.objects.bulk_create(
                [
                    Event(
                        user={
                            "pk": str(uuid4()),
                            "name": str(uuid4()),
                            "username": str(uuid4()),
                            "email": f"{uuid4()}@example.org",
                        },
                        action="custom_benchmark",
                        app="tests_benchmarks",
                        context={
                            str(uuid4()): str(uuid4()),
                            str(uuid4()): str(uuid4()),
                            str(uuid4()): str(uuid4()),
                            str(uuid4()): str(uuid4()),
                            str(uuid4()): str(uuid4()),
                        },
                        client_ip="192.0.2.42",
                    )
                    for _ in range(event_count)
                ]
            )


def delete():
    Tenant.objects.exclude(schema_name="public").delete()


def main(action: str):
    match action:
        case "create":
            login()
            provider_oauth2()
            user_list()
            group_list()
            event_list()
        case "delete":
            delete()
        case _:
            print("Unknown action. Should be create or delete")
            exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        action = "create"
    else:
        action = sys.argv[1]
    main(action)
