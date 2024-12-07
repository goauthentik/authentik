#!/usr/bin/env python3
import random
import sys
from collections.abc import Iterable
from multiprocessing import Process
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


class TestSuite:
    TEST_NAME: str
    TEST_CASES: Iterable[Iterable[int | str | bool]]

    @classmethod
    def get_testcases(cls):
        return [cls(params) for params in cls.TEST_CASES]

    def __init__(self, params: Iterable[int | str | bool]):
        self.params = params

    def __str__(self):
        return (
            "-".join([self.TEST_NAME] + [str(param) for param in self.params])
            .replace("_", "-")
            .lower()
        )

    @property
    def schema_name(self):
        return f"t_{str(self).replace('-', '_')}"

    @property
    def domain_name(self):
        return f"{str(self)}.{host}"

    def create(self):
        created = False
        t = Tenant.objects.filter(schema_name=self.schema_name).first()
        if not t:
            created = True
            t = Tenant.objects.create(schema_name=self.schema_name, name=uuid4())
        Domain.objects.get_or_create(tenant=t, domain=self.domain_name)
        if created:
            with t:
                self.create_data(*self.params)

    def create_data(self):
        raise NotImplementedError

    def delete(self):
        Tenant.objects.filter(schema_name=self.schema_name).delete()


class UserList(TestSuite):
    TEST_NAME = "user-list"
    TEST_CASES = [
        (1000, 0, 0),
        (10000, 0, 0),
        (1000, 3, 0),
        (10000, 3, 0),
        (1000, 20, 0),
        (10000, 20, 0),
        (1000, 20, 3),
        (10000, 20, 3),
    ]

    def create_data(self, user_count: int, groups_per_user: int, parents_per_group: int):
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
                    Group.objects.exclude(name="authentik Admins").order_by("?")[:groups_per_user]
                )


class GroupList(TestSuite):
    TEST_NAME = "group-list"
    TEST_CASES = [
        (1000, 0, False),
        (10000, 0, False),
        (1000, 1000, False),
        (1000, 10000, False),
        (1000, 0, True),
        (10000, 0, True),
    ]

    def create_data(self, group_count, users_per_group, with_parent):
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
            parents = Group.objects.bulk_create([Group(name=uuid4()) for _ in range(group_count)])
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


class Login(TestSuite):
    TEST_NAME = "login"
    TEST_CASES = [
        ("no-mfa",),
        ("with-mfa",),
    ]

    def create_data(self, mfa: str):
        user = User(username="test", name=uuid4())
        user.set_password("verySecurePassword")
        user.save()

        if mfa == "with-mfa":
            device = user.staticdevice_set.create()
            # Multiple token with same token for all the iterations in the test
            device.token_set.bulk_create(
                [StaticToken(device=device, token=f"staticToken") for _ in range(1_000_000)]
            )


class ProviderOauth2(TestSuite):
    TEST_NAME = "provider-oauth2"
    TEST_CASES = [
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

    def create_data(
        self, user_policies_count: int, group_policies_count: int, expression_policies_count: int
    ):
        user = User(username="test", name=uuid4())
        user.set_password("verySecurePassword")
        user.save()

        provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            signing_key=CertificateKeyPair.objects.get(name="authentik Self-signed Certificate"),
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


class EventList(TestSuite):
    TEST_NAME = "event-list"
    TEST_CASES = [
        (1_000,),
        (10_000,),
        (100_000,),
        (1_000_000,),
    ]

    def create_data(self, event_count: int):
        for _ in range(event_count // 1000):
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
                    for _ in range(1000)
                ]
            )


class UserGroupCreate(TestSuite):
    TEST_NAME = "user-group-create"
    TEST_CASES = [
        (),
    ]

    def create_data(self):
        pass


def main(action: str, selected_suite: str | None = None):
    testsuites = TestSuite.__subclasses__()
    testcases = []
    for testsuite in testsuites:
        testcases += testsuite.get_testcases()

    match action:
        case "create":
            to_create = []
            for testcase in testcases:
                if selected_suite and testcase.TEST_NAME != selected_suite:
                    continue
                testcase.create()
            #     to_create.append(testcase)
            # processes = [Process(target=testcase.create) for testcase in to_create]
            # for p in processes:
            #     p.start()
            # for p in processes:
            #     p.join()
        case "list":
            print(*[testsuite.TEST_NAME for testsuite in testsuites], sep="\n")
        case "delete":
            for testcase in testcases:
                if selected_suite and testcase.TEST_NAME != selected_suite:
                    continue
                testcase.delete()
        case _:
            print("Unknown action. Should be create, list or delete")
            exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        action = "create"
    else:
        action = sys.argv[1]
    if len(sys.argv) < 3:
        testsuite = None
    else:
        testsuite = sys.argv[2]
    main(action, testsuite)
