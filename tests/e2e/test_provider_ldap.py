"""LDAP and Outpost e2e tests"""
from dataclasses import asdict
from sys import platform
from time import sleep
from unittest.case import skipUnless

from docker.client import DockerClient, from_env
from docker.models.containers import Container
from guardian.shortcuts import get_anonymous_user
from ldap3 import ALL, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPInvalidCredentialsResult

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application, User
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostConfig, OutpostType
from authentik.providers.ldap.models import APIAccessMode, LDAPProvider
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestProviderLDAP(SeleniumTestCase):
    """LDAP and Outpost e2e tests"""

    ldap_container: Container

    def tearDown(self) -> None:
        super().tearDown()
        self.output_container_logs(self.ldap_container)
        self.ldap_container.kill()

    def start_ldap(self, outpost: Outpost) -> Container:
        """Start ldap container based on outpost created"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image=self.get_container_image("ghcr.io/goauthentik/dev-ldap"),
            detach=True,
            network_mode="host",
            environment={
                "AUTHENTIK_HOST": self.live_server_url,
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )
        return container

    def _prepare(self) -> User:
        """prepare user, provider, app and container"""
        self.user.attributes["extraAttribute"] = "bar"
        self.user.save()

        ldap: LDAPProvider = LDAPProvider.objects.create(
            name="ldap_provider",
            authorization_flow=Flow.objects.get(slug="default-authentication-flow"),
            search_group=self.user.ak_groups.first(),
            search_mode=APIAccessMode.CACHED,
        )
        # we need to create an application to actually access the ldap
        Application.objects.create(name="ldap", slug="ldap", provider=ldap)
        outpost: Outpost = Outpost.objects.create(
            name="ldap_outpost",
            type=OutpostType.LDAP,
            _config=asdict(OutpostConfig(log_level="debug")),
        )
        outpost.providers.add(ldap)

        self.ldap_container = self.start_ldap(outpost)

        # Wait until outpost healthcheck succeeds
        healthcheck_retries = 0
        while healthcheck_retries < 50:
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen:
                    break
            healthcheck_retries += 1
            sleep(0.5)
        sleep(5)
        return outpost

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_ldap_bind_success(self):
        """Test simple bind"""
        self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,DC=ldap,DC=goauthentik,DC=io",
            password=self.user.username,
        )
        _connection.bind()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            )
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_ldap_bind_success_ssl(self):
        """Test simple bind with ssl"""
        self._prepare()
        server = Server("ldaps://localhost:6636", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,DC=ldap,DC=goauthentik,DC=io",
            password=self.user.username,
        )
        _connection.bind()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            )
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_ldap_bind_success_starttls(self):
        """Test simple bind with ssl"""
        self._prepare()
        server = Server("ldap://localhost:3389")
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,DC=ldap,DC=goauthentik,DC=io",
            password=self.user.username,
        )
        _connection.start_tls()
        _connection.bind()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            )
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_ldap_bind_fail(self):
        """Test simple bind (failed)"""
        self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,DC=ldap,DC=goauthentik,DC=io",
            password=self.user.username + "fqwerwqer",
        )
        with self.assertRaises(LDAPInvalidCredentialsResult):
            _connection.bind()
        anon = get_anonymous_user()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN_FAILED,
                user={"pk": anon.pk, "email": anon.email, "username": anon.username},
            ).exists(),
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_outposts")
    def test_ldap_bind_search(self):
        """Test simple bind + search"""
        # Remove akadmin to ensure list is correct
        # Remove user before starting container so it's not cached
        User.objects.filter(username="akadmin").delete()

        outpost = self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
            password=self.user.username,
        )
        _connection.bind()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            )
        )

        embedded_account = Outpost.objects.filter(managed=MANAGED_OUTPOST).first().user

        _connection.search(
            "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
            "(objectClass=user)",
            search_scope=SUBTREE,
            attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
        )
        response: dict = _connection.response
        # Remove raw_attributes to make checking easier
        for obj in response:
            del obj["raw_attributes"]
            del obj["raw_dn"]
        o_user = outpost.user
        self.assertCountEqual(
            response,
            [
                {
                    "dn": f"cn={o_user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": o_user.username,
                        "sAMAccountName": o_user.username,
                        "uid": o_user.uid,
                        "name": o_user.name,
                        "displayName": o_user.name,
                        "sn": o_user.name,
                        "mail": "",
                        "objectClass": [
                            "user",
                            "organizationalPerson",
                            "inetOrgPerson",
                            "goauthentik.io/ldap/user",
                            "posixAccount",
                        ],
                        "uidNumber": 2000 + o_user.pk,
                        "gidNumber": 2000 + o_user.pk,
                        "memberOf": [],
                        "homeDirectory": f"/home/{o_user.username}",
                        "ak-active": True,
                        "ak-superuser": False,
                        "goauthentikio-user-override-ips": True,
                        "goauthentikio-user-service-account": True,
                    },
                    "type": "searchResEntry",
                },
                {
                    "dn": f"cn={embedded_account.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": embedded_account.username,
                        "sAMAccountName": embedded_account.username,
                        "uid": embedded_account.uid,
                        "name": embedded_account.name,
                        "displayName": embedded_account.name,
                        "sn": embedded_account.name,
                        "mail": "",
                        "objectClass": [
                            "user",
                            "organizationalPerson",
                            "inetOrgPerson",
                            "goauthentik.io/ldap/user",
                            "posixAccount",
                        ],
                        "uidNumber": 2000 + embedded_account.pk,
                        "gidNumber": 2000 + embedded_account.pk,
                        "memberOf": [],
                        "homeDirectory": f"/home/{embedded_account.username}",
                        "ak-active": True,
                        "ak-superuser": False,
                        "goauthentikio-user-override-ips": True,
                        "goauthentikio-user-service-account": True,
                    },
                    "type": "searchResEntry",
                },
                {
                    "dn": f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": self.user.username,
                        "sAMAccountName": self.user.username,
                        "uid": self.user.uid,
                        "name": self.user.name,
                        "displayName": self.user.name,
                        "sn": self.user.name,
                        "mail": self.user.email,
                        "objectClass": [
                            "user",
                            "organizationalPerson",
                            "inetOrgPerson",
                            "goauthentik.io/ldap/user",
                            "posixAccount",
                        ],
                        "uidNumber": 2000 + self.user.pk,
                        "gidNumber": 2000 + self.user.pk,
                        "memberOf": [
                            f"cn={group.name},ou=groups,dc=ldap,dc=goauthentik,dc=io"
                            for group in self.user.ak_groups.all()
                        ],
                        "homeDirectory": f"/home/{self.user.username}",
                        "ak-active": True,
                        "ak-superuser": True,
                        "extraAttribute": ["bar"],
                    },
                    "type": "searchResEntry",
                },
            ],
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_outposts")
    def test_ldap_schema(self):
        """Test LDAP Schema"""
        self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
            password=self.user.username,
        )
        _connection.bind()
        self.assertIsNotNone(server.schema)
        self.assertTrue(server.schema.is_valid())
        self.assertIsNotNone(server.schema.object_classes["goauthentik.io/ldap/user"])

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_outposts")
    def test_ldap_search_attrs_filter(self):
        """Test search with attributes filtering"""
        # Remove akadmin to ensure list is correct
        # Remove user before starting container so it's not cached
        User.objects.filter(username="akadmin").delete()

        outpost = self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
            password=self.user.username,
        )
        _connection.bind()
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            )
        )

        embedded_account = Outpost.objects.filter(managed=MANAGED_OUTPOST).first().user

        _connection.search(
            "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
            "(objectClass=user)",
            search_scope=SUBTREE,
            attributes=["cn"],
        )
        response: dict = _connection.response
        # Remove raw_attributes to make checking easier
        for obj in response:
            del obj["raw_attributes"]
            del obj["raw_dn"]
        o_user = outpost.user
        self.assertCountEqual(
            response,
            [
                {
                    "dn": f"cn={o_user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": o_user.username,
                    },
                    "type": "searchResEntry",
                },
                {
                    "dn": f"cn={embedded_account.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": embedded_account.username,
                    },
                    "type": "searchResEntry",
                },
                {
                    "dn": f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                    "attributes": {
                        "cn": self.user.username,
                    },
                    "type": "searchResEntry",
                },
            ],
        )
