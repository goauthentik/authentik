"""LDAP and Outpost e2e tests"""

from dataclasses import asdict
from pathlib import Path
from tempfile import gettempdir
from time import sleep
from unittest.mock import MagicMock, patch

from ldap3 import (
    ALL,
    ALL_ATTRIBUTES,
    ALL_OPERATIONAL_ATTRIBUTES,
    EXTERNAL,
    SASL,
    SUBTREE,
    Connection,
    Server,
    Tls,
)
from ldap3.core.exceptions import LDAPInvalidCredentialsResult, LDAPSessionTerminatedByServerError

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.models import Application, AuthenticatedSession, User
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.endpoints.models import StageMode
from authentik.enterprise.stages.mtls.models import MutualTLSStage
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost, OutpostConfig, OutpostType
from authentik.providers.ldap.models import APIAccessMode, LDAPProvider
from authentik.stages.user_login.models import UserLoginStage
from tests.decorators import retry
from tests.live import ChannelsE2ETestCase


def clean_response(response):
    # Remove raw_attributes to make checking easier
    for obj in response:
        del obj["raw_attributes"]
        del obj["raw_dn"]
        obj["attributes"] = dict(obj["attributes"])
        obj["attributes"].pop("uid", None)
    return response


class TestProviderLDAP(ChannelsE2ETestCase):
    """LDAP and Outpost e2e tests"""

    def setUp(self):
        super().setUp()
        self.kp = create_test_cert()
        self.cert = Path(gettempdir()) / generate_id()
        with open(self.cert, "w") as _cert:
            _cert.write(self.kp.certificate_data)
        self.key = Path(gettempdir()) / generate_id()
        with open(self.key, "w") as _key:
            _key.write(self.kp.key_data)

    def assert_list_dict_equal(self, expected: list[dict], actual: list[dict], match_key="dn"):
        """Assert a list of dictionaries is identical, ignoring the ordering of items"""
        self.assertEqual(len(expected), len(actual))
        for res_item in actual:
            all_matching = [x for x in expected if x[match_key] == res_item[match_key]]
            self.assertEqual(len(all_matching), 1)
            matching = all_matching[0]
            self.assertDictEqual(res_item, matching)

    def start_ldap(self, outpost: Outpost):
        """Start ldap container based on outpost created"""
        self.run_container(
            image=self.get_container_image("ghcr.io/goauthentik/dev-ldap"),
            ports={
                "3389": "3389",
                "6636": "6636",
            },
            environment={
                "AUTHENTIK_TOKEN": outpost.token.key,
            },
        )

    def _prepare(self, **kwargs) -> User:
        """prepare user, provider, app and container"""
        self.user.attributes["extraAttribute"] = "bar"
        self.user.save()

        kwargs.setdefault(
            "authorization_flow", Flow.objects.get(slug="default-authentication-flow")
        )

        ldap = LDAPProvider.objects.create(
            name=generate_id(), search_mode=APIAccessMode.CACHED, **kwargs
        )
        self.user.assign_perms_to_managed_role(
            "authentik_providers_ldap.search_full_directory", ldap
        )
        # we need to create an application to actually access the ldap
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=ldap)
        outpost: Outpost = Outpost.objects.create(
            name=generate_id(),
            type=OutpostType.LDAP,
            _config=asdict(OutpostConfig(log_level="debug")),
        )
        outpost.providers.add(ldap)

        self.start_ldap(outpost)
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first()
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first()
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first()
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_ldap_bind_success_starttls_sasl(self):
        """Test SASL bind with ssl"""
        # Create flow with MTLS Stage
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        mtls_stage = MutualTLSStage.objects.create(
            name=generate_id(),
            mode=StageMode.REQUIRED,
        )
        mtls_stage.certificate_authorities.add(self.kp)
        login_stage = UserLoginStage.objects.create(
            name=generate_id(),
        )
        FlowStageBinding.objects.create(target=flow, stage=mtls_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=login_stage, order=1)

        self._prepare(authorization_flow=flow, certificate=self.kp)

        tls = Tls(
            local_private_key_file=self.key,
            local_certificate_file=self.cert,
        )
        server = Server("ldap://localhost:3389", tls=tls)
        _connection = Connection(
            server,
            version=3,
            raise_exceptions=True,
            authentication=SASL,
            sasl_mechanism=EXTERNAL,
            sasl_credentials=f"dn:cn={self.user.username},ou=users,DC=ldap,DC=goauthentik,DC=io",
        )
        _connection.start_tls()
        with (
            patch(
                "authentik.enterprise.stages.mtls.stage.MTLSStageView.validate_cert",
                MagicMock(return_value=self.kp.certificate),
            ),
            patch(
                "authentik.enterprise.stages.mtls.stage.MTLSStageView.check_if_user",
                MagicMock(return_value=self.user),
            ) as check_if_user,
        ):
            _connection.bind()
            check_if_user.assert_called_once_with(self.kp.certificate)
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            user={
                "pk": self.user.pk,
                "email": self.user.email,
                "username": self.user.username,
            },
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["auth_method"], "mtls")
        self.assertEqual(
            event.context["auth_method_args"]["certificate"]["fingerprint_sha256"],
            self.kp.fingerprint_sha256,
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN_FAILED,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first(),
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_tenants")
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first()
        )

        embedded_account = Outpost.objects.filter(managed=MANAGED_OUTPOST).first().user

        _connection.search(
            "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
            "(objectClass=user)",
            search_scope=SUBTREE,
            attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
        )
        response = clean_response(_connection.response)
        o_user = outpost.user
        expected = [
            {
                "dn": f"cn={o_user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                "attributes": {
                    "cn": o_user.username,
                    "sAMAccountName": o_user.username,
                    "name": o_user.name,
                    "displayName": o_user.name,
                    "sn": o_user.name,
                    "mail": "",
                    "objectClass": [
                        "top",
                        "person",
                        "organizationalPerson",
                        "inetOrgPerson",
                        "user",
                        "posixAccount",
                        "goauthentik.io/ldap/user",
                    ],
                    "uidNumber": 2000 + o_user.pk,
                    "gidNumber": 2000 + o_user.pk,
                    "memberOf": [],
                    "homeDirectory": f"/home/{o_user.username}",
                    "ak-active": True,
                    "ak-superuser": False,
                    "pwdChangedTime": o_user.password_change_date.replace(microsecond=0),
                    "createTimestamp": o_user.date_joined.replace(microsecond=0),
                    "modifyTimestamp": o_user.last_updated.replace(microsecond=0),
                },
                "type": "searchResEntry",
            },
            {
                "dn": f"cn={embedded_account.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                "attributes": {
                    "cn": embedded_account.username,
                    "sAMAccountName": embedded_account.username,
                    "name": embedded_account.name,
                    "displayName": embedded_account.name,
                    "sn": embedded_account.name,
                    "mail": "",
                    "objectClass": [
                        "top",
                        "person",
                        "organizationalPerson",
                        "inetOrgPerson",
                        "user",
                        "posixAccount",
                        "goauthentik.io/ldap/user",
                    ],
                    "uidNumber": 2000 + embedded_account.pk,
                    "gidNumber": 2000 + embedded_account.pk,
                    "memberOf": [],
                    "homeDirectory": f"/home/{embedded_account.username}",
                    "ak-active": True,
                    "ak-superuser": False,
                    "pwdChangedTime": embedded_account.password_change_date.replace(microsecond=0),
                    "createTimestamp": embedded_account.date_joined.replace(microsecond=0),
                    "modifyTimestamp": embedded_account.last_updated.replace(microsecond=0),
                },
                "type": "searchResEntry",
            },
            {
                "dn": f"cn={self.user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                "attributes": {
                    "cn": self.user.username,
                    "sAMAccountName": self.user.username,
                    "name": self.user.name,
                    "displayName": self.user.name,
                    "sn": self.user.name,
                    "mail": self.user.email,
                    "objectClass": [
                        "top",
                        "person",
                        "organizationalPerson",
                        "inetOrgPerson",
                        "user",
                        "posixAccount",
                        "goauthentik.io/ldap/user",
                    ],
                    "uidNumber": 2000 + self.user.pk,
                    "gidNumber": 2000 + self.user.pk,
                    "memberOf": [
                        f"cn={group.name},ou=groups,dc=ldap,dc=goauthentik,dc=io"
                        for group in self.user.groups.all()
                    ],
                    "homeDirectory": f"/home/{self.user.username}",
                    "ak-active": True,
                    "ak-superuser": True,
                    "extraAttribute": ["bar"],
                    "pwdChangedTime": self.user.password_change_date.replace(microsecond=0),
                    "createTimestamp": self.user.date_joined.replace(microsecond=0),
                    "modifyTimestamp": self.user.last_updated.replace(microsecond=0),
                },
                "type": "searchResEntry",
            },
        ]
        self.assert_list_dict_equal(expected, response)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_tenants")
    @reconcile_app("authentik_outposts")
    def test_ldap_bind_search_no_perms(self):
        """Test simple bind + search"""
        user = create_test_user()
        self._prepare()
        server = Server("ldap://localhost:3389", get_info=ALL)
        _connection = Connection(
            server,
            raise_exceptions=True,
            user=f"cn={user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
            password=user.username,
        )
        _connection.bind()
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": user.pk,
                    "email": user.email,
                    "username": user.username,
                },
            ).first()
        )

        _connection.search(
            "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
            "(objectClass=user)",
            search_scope=SUBTREE,
            attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
        )
        response = clean_response(_connection.response)
        expected = [
            {
                "dn": f"cn={user.username},ou=users,dc=ldap,dc=goauthentik,dc=io",
                "attributes": {
                    "cn": user.username,
                    "sAMAccountName": user.username,
                    "name": user.name,
                    "displayName": user.name,
                    "sn": user.name,
                    "mail": user.email,
                    "objectClass": [
                        "top",
                        "person",
                        "organizationalPerson",
                        "inetOrgPerson",
                        "user",
                        "posixAccount",
                        "goauthentik.io/ldap/user",
                    ],
                    "uidNumber": 2000 + user.pk,
                    "gidNumber": 2000 + user.pk,
                    "memberOf": [
                        f"cn={group.name},ou=groups,dc=ldap,dc=goauthentik,dc=io"
                        for group in user.groups.all()
                    ],
                    "homeDirectory": f"/home/{user.username}",
                    "ak-active": True,
                    "ak-superuser": False,
                    "pwdChangedTime": user.password_change_date.replace(microsecond=0),
                    "createTimestamp": user.date_joined.replace(microsecond=0),
                    "modifyTimestamp": user.last_updated.replace(microsecond=0),
                },
                "type": "searchResEntry",
            },
        ]
        self.assert_list_dict_equal(expected, response)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_tenants")
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
    @reconcile_app("authentik_tenants")
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
        self.assertIsNotNone(
            Event.objects.filter(
                action=EventAction.LOGIN,
                user={
                    "pk": self.user.pk,
                    "email": self.user.email,
                    "username": self.user.username,
                },
            ).first()
        )

        embedded_account = Outpost.objects.filter(managed=MANAGED_OUTPOST).first().user

        _connection.search(
            "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
            "(objectClass=user)",
            search_scope=SUBTREE,
            attributes=["cn"],
        )
        response = clean_response(_connection.response)

        o_user = outpost.user
        self.assert_list_dict_equal(
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
            response,
        )

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @reconcile_app("authentik_tenants")
    @reconcile_app("authentik_outposts")
    def test_ldap_bind_logout_search(self):
        """Test bind + session deletion -> failed search"""
        self._prepare()
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
        c, _ = AuthenticatedSession.objects.filter(user_id=self.user.pk).delete()
        self.assertGreaterEqual(c, 1)
        # Give the sign out signal time to propagate
        sleep(3)

        with self.assertRaises(LDAPSessionTerminatedByServerError):
            _connection.search(
                "ou=Users,DC=ldaP,dc=goauthentik,dc=io",
                "(objectClass=user)",
                search_scope=SUBTREE,
                attributes=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES],
            )
