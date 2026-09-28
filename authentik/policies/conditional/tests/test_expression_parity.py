"""Expression policies from blueprints and documentation, re-built as conditional policies.

Each case runs the original expression policy and the conditional policy against the same
requests and checks that both return the same result and messages."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from authentik.core.models import USER_ATTRIBUTE_CHANGE_EMAIL, Group, User
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction
from authentik.flows.planner import FlowPlan
from authentik.lib.generators import generate_id
from authentik.policies.conditional.models import ConditionalPolicy, MissingBehavior
from authentik.policies.conditional.tests.test_evaluator import cond, group, tree
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.types import PolicyRequest
from authentik.stages.authenticator_static.models import StaticDevice
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.tenants.utils import get_current_tenant


class _BlueprintLoader(yaml.SafeLoader):
    """Load blueprints without resolving their tags"""


_BlueprintLoader.add_multi_constructor(
    "!",
    lambda loader, suffix, node: (
        loader.construct_scalar(node)
        if isinstance(node, yaml.ScalarNode)
        else (
            loader.construct_sequence(node)
            if isinstance(node, yaml.SequenceNode)
            else loader.construct_mapping(node)
        )
    ),
)


def blueprint_policy(path: str, name: str) -> dict:
    """Attributes of the conditional policy `name` in the blueprint at `path`"""
    with open(Path(settings.BASE_DIR) / "blueprints" / path, encoding="utf-8") as blueprint:
        data = yaml.load(blueprint, Loader=_BlueprintLoader)  # noqa: S506
    entries = data["entries"]
    if isinstance(entries, dict):
        entries = [entry for group in entries.values() for entry in group]
    for entry in entries:
        if (
            entry.get("model") == "authentik_policies_conditional.conditionalpolicy"
            and entry.get("state", "present") != "absent"
            and name in (entry.get("identifiers", {}).get("name"), entry["attrs"].get("name"))
        ):
            return entry["attrs"]
    raise ValueError(f"Policy {name} not found in {path}")


def neg(node: dict) -> dict:
    return {"type": "group", "op": "none", "children": [node]}


def var(key: str, **kwargs) -> dict:
    return {"type": "variable", "variable": {"key": key, **kwargs}}


@dataclass
class Scenario:
    name: str
    user: User | AnonymousUser | None = None
    context: dict[str, Any] = field(default_factory=dict)
    # Put `context` into a flow plan, like the flow planner and executor do
    in_flow: bool = True
    remote_addr: str = "10.1.2.3"
    http_user: User | AnonymousUser | None = None
    setup: Callable[[User], None] | None = None


class TestExpressionParity(TestCase):
    """Conditional policies behave like the expression policies they replace"""

    def setUp(self):
        self.user = create_test_user()

    def build_request(self, scenario: Scenario) -> PolicyRequest:
        user = scenario.user or self.user
        if scenario.setup:
            scenario.setup(user)
        request = PolicyRequest(user)
        http_request = RequestFactory().get("/", REMOTE_ADDR=scenario.remote_addr)
        http_request.user = scenario.http_user or user
        http_request.tenant = get_current_tenant()
        request.http_request = http_request
        context = dict(scenario.context)
        if scenario.in_flow:
            plan = FlowPlan(flow_pk=generate_id())
            plan.context = context
            context = {**context, "flow_plan": plan, "pending_user": user}
            plan.context.setdefault("pending_user", user)
        request.context = context
        return request

    def assertParity(  # noqa: N802
        self,
        expression: str,
        root: dict | None,
        scenarios: list[Scenario],
        expected: list[bool | None],
        compare_messages: bool = True,
        blueprint: tuple[str, str] | None = None,
        **kwargs,
    ):
        """Compare an expression with a conditional policy, which checks the condition `root`
        or is loaded from `blueprint` (path and name of the policy)"""
        expression_policy = ExpressionPolicy(name=generate_id(), expression=expression)
        if blueprint:
            attrs = blueprint_policy(*blueprint)
            kwargs.setdefault("missing_behavior", attrs.get("missing_behavior", "fail"))
            conditional = ConditionalPolicy(name=generate_id(), actions=attrs["actions"], **kwargs)
        else:
            conditional = ConditionalPolicy(name=generate_id(), actions=tree(root), **kwargs)
        for scenario, passing in zip(scenarios, expected, strict=True):
            with self.subTest(scenario=scenario.name):
                conditional_result = conditional.passes(self.build_request(scenario))
                if passing is None:
                    # Known difference, where the conditional policy is more correct
                    continue
                expression_result = expression_policy.passes(self.build_request(scenario))
                self.assertEqual(expression_result.passing, passing, "expression")
                self.assertEqual(conditional_result.passing, passing, "conditional")
                if compare_messages:
                    self.assertEqual(
                        list(expression_result.messages), list(conditional_result.messages)
                    )

    # Blueprints

    def test_default_authentication_flow_password_stage(self):
        """blueprints/default/flow-default-authentication-flow.yaml"""

        def authenticated(user):
            user.backend = "foo"

        self.assertParity(
            """flow_plan = request.context.get("flow_plan")
if not flow_plan:
    return True
return not hasattr(flow_plan.context.get("pending_user"), "backend")""",
            None,
            [
                Scenario("not authenticated"),
                Scenario("authenticated", user=create_test_user(), setup=authenticated),
                Scenario("no flow", in_flow=False),
            ],
            [True, False, True],
            blueprint=(
                "default/flow-default-authentication-flow.yaml",
                "default-authentication-flow-password-stage",
            ),
        )

    def test_default_authentication_flow_authenticator_validate(self):
        """blueprints/default/flow-default-authentication-flow.yaml"""
        self.assertParity(
            """flow_plan = request.context.get("flow_plan")
if not flow_plan:
    return True
return not (flow_plan.context.get("auth_method") == "auth_webauthn_pwl")""",
            None,
            [
                Scenario("password", context={"auth_method": "password"}),
                Scenario("passwordless", context={"auth_method": "auth_webauthn_pwl"}),
                Scenario("not set"),
            ],
            [True, False, True],
            blueprint=(
                "default/flow-default-authentication-flow.yaml",
                "default-authentication-flow-authenticator-validate-stage",
            ),
        )

    def test_default_source_if_sso(self):
        """blueprints/default/flow-default-source-{authentication,enrollment}.yaml"""
        self.assertParity(
            "return ak_is_sso_flow",
            None,
            [
                Scenario("sso", context={"is_sso": True}),
                Scenario("not sso", context={"is_sso": False}),
                Scenario("not set"),
            ],
            [True, False, False],
            blueprint=(
                "default/flow-default-source-authentication.yaml",
                "default-source-authentication-if-sso",
            ),
        )

    def test_default_source_enrollment_if_username(self):
        """blueprints/default/flow-default-source-enrollment.yaml"""
        self.assertParity(
            "return 'username' not in context.get('prompt_data', {})",
            None,
            [
                Scenario("no username", context={"prompt_data": {"email": "foo@bar.baz"}}),
                Scenario("username", context={"prompt_data": {"username": "foo"}}),
            ],
            [True, False],
            blueprint=(
                "default/flow-default-source-enrollment.yaml",
                "default-source-enrollment-if-username",
            ),
        )

    def test_default_user_settings_authorization(self):
        """blueprints/default/flow-default-user-settings-flow.yaml"""

        def allow_email_change(user):
            user.attributes[USER_ATTRIBUTE_CHANGE_EMAIL] = True
            user.save()

        user = create_test_user()

        def prompt(target: User = user, **overrides):
            return {
                "prompt_data": {
                    "email": target.email,
                    "name": target.name,
                    "username": target.username,
                    **overrides,
                }
            }

        other = create_test_user()
        no_email = create_test_user(email="")

        self.assertParity(
            """from authentik.core.models import (
    USER_ATTRIBUTE_CHANGE_EMAIL,
    USER_ATTRIBUTE_CHANGE_NAME,
    USER_ATTRIBUTE_CHANGE_USERNAME
)
prompt_data = request.context.get("prompt_data")

if not request.user.group_attributes(request.http_request).get(
    USER_ATTRIBUTE_CHANGE_EMAIL, request.http_request.tenant.default_user_change_email
):
    if prompt_data.get("email") != request.user.email:
        ak_message("Not allowed to change email address.")
        return False

if not request.user.group_attributes(request.http_request).get(
    USER_ATTRIBUTE_CHANGE_NAME, request.http_request.tenant.default_user_change_name
):
    if prompt_data.get("name") != request.user.name:
        ak_message("Not allowed to change name.")
        return False

if not request.user.group_attributes(request.http_request).get(
    USER_ATTRIBUTE_CHANGE_USERNAME, request.http_request.tenant.default_user_change_username
):
    if prompt_data.get("username") != request.user.username:
        ak_message("Not allowed to change username.")
        return False

return True""",
            None,
            [
                Scenario("unchanged", user=user, context=prompt()),
                # Changing the name is allowed by default
                Scenario("allowed change", user=user, context=prompt(name="New Name")),
                # Changing the email address is not allowed by default
                Scenario("denied change", user=user, context=prompt(email="new@bar.baz")),
                Scenario(
                    "allowed by attribute",
                    user=other,
                    context=prompt(other, email="new@bar.baz"),
                    setup=allow_email_change,
                ),
                # Users without email address can change their name
                Scenario(
                    "no email",
                    user=no_email,
                    context=prompt(no_email, name="New Name"),
                ),
            ],
            [True, True, False, True, True],
            blueprint=(
                "default/flow-default-user-settings-flow.yaml",
                "default-user-settings-authorization",
            ),
        )

    def test_login_2fa_not_app_password(self):
        """blueprints/example/flows-login-2fa.yaml"""
        self.assertParity(
            'return context.get("auth_method") != "app_password"',
            None,
            [
                Scenario("app password", context={"auth_method": "app_password"}),
                Scenario("password", context={"auth_method": "password"}),
                Scenario("not set"),
            ],
            [False, True, True],
            blueprint=("example/flows-login-2fa.yaml", "test-not-app-password"),
        )

    def test_recovery_skip_if_restored(self):
        """blueprints/example/flows-recovery-email-*.yaml"""
        self.assertParity(
            "return bool(request.context.get('is_restored', True))",
            None,
            [
                Scenario("not set"),
                Scenario("restored", context={"is_restored": "token"}),
                Scenario("not restored", context={"is_restored": None}),
            ],
            [True, True, False],
            blueprint=(
                "example/flows-recovery-email-verification.yaml",
                "default-recovery-skip-if-restored",
            ),
        )

    def test_account_lockdown_admin(self):
        """blueprints/example/flow-default-account-lockdown.yaml"""
        admin = create_test_user()
        self.assertParity(
            """actor_uuid = str(getattr(request.http_request.user, "pk", ""))
target_uuid = str(getattr(request.user, "pk", ""))
return bool(target_uuid) and target_uuid != actor_uuid""",
            None,
            [
                Scenario("self service"),
                Scenario("admin", http_user=admin),
                Scenario("anonymous actor", http_user=AnonymousUser()),
            ],
            [False, True, True],
            blueprint=(
                "example/flow-default-account-lockdown.yaml",
                "default-account-lockdown-admin-policy",
            ),
        )

    def test_oobe_base_url_valid(self):
        """blueprints/default/flow-oobe.yaml"""
        self.assertParity(
            """from django.core.exceptions import ValidationError
from authentik.tenants.models import Tenant
from authentik.tenants.utils import normalize_base_url

base_url = normalize_base_url((request.context.get("prompt_data") or {}).get("base_url"))
if not base_url:
    return True
try:
    Tenant._meta.get_field("base_url").run_validators(base_url)
except ValidationError as exc:
    ak_message(exc.messages[0])
    return False
return True""",
            group(
                "any",
                cond("prompt_data", "is_not_set", param="base_url"),
                cond("prompt_data", "is_url", param="base_url", cast="string"),
            ),
            [
                Scenario("not set", context={"prompt_data": {}}),
                Scenario("valid", context={"prompt_data": {"base_url": "https://auth.local"}}),
                Scenario("invalid", context={"prompt_data": {"base_url": "not a url"}}),
            ],
            [True, True, False],
            failure_message="Enter a valid URL, for example https://authentik.company",
        )

    # Documentation

    def test_docs_sms_phone_number(self):
        """add-secure-apps/flows-stages/stages/authenticator_sms"""
        self.assertParity(
            """phone_number = regex_replace(request.context["prompt_data"]["phone"], r"\\s+", "")

if phone_number.startswith("+1234"):
    return True
ak_message("Invalid phone number or missing region code")
return False""",
            cond(
                "prompt_data",
                "matches",
                r"^\s*\+\s*1\s*2\s*3\s*4",
                param="phone",
                cast="string",
            ),
            [
                Scenario("valid", context={"prompt_data": {"phone": "+1 234 5678"}}),
                Scenario("invalid", context={"prompt_data": {"phone": "+49 123 4567"}}),
            ],
            [True, False],
            failure_message="Invalid phone number or missing region code",
        )

    def test_docs_authenticator_validate_two_types(self):
        """add-secure-apps/flows-stages/stages/authenticator_validate"""
        user = create_test_user()

        def two_devices(user):
            TOTPDevice.objects.create(user=user, name="totp", confirmed=True)
            StaticDevice.objects.create(user=user, name="static", confirmed=True)

        self.assertParity(
            """from authentik.stages.authenticator import devices_for_user

pending_user = request.context.get("pending_user")
if not pending_user or not pending_user.pk:
    return False

device_types = {
    device.__class__.__name__.lower().replace("device", "")
    for device in devices_for_user(pending_user, confirmed=True)
}

return len(device_types) >= 2""",
            cond("user.authenticator_types", "length_gt", 1),
            [Scenario("no devices"), Scenario("two types", user=user, setup=two_devices)],
            [False, True],
        )

    def test_docs_client_ip_network(self):
        """stages/deny, policies/types/expression/reference"""
        self.assertParity(
            """from ipaddress import ip_network

return ak_client_ip in ip_network("10.0.0.0/24")""",
            cond("request.client_ip", "in_network", ["10.0.0.0/24"]),
            [
                Scenario("inside", remote_addr="10.0.0.5"),
                Scenario("outside", remote_addr="192.0.2.1"),
            ],
            [True, False],
        )

    def test_docs_client_ip_private(self):
        """policies/types/expression/reference"""
        self.assertParity(
            "return ak_client_ip.is_private",
            cond("request.client_ip", "is_private"),
            [
                Scenario("private", remote_addr="10.0.0.5"),
                Scenario("public", remote_addr="8.8.8.8"),
            ],
            [True, False],
        )

    def test_docs_deny_inactive(self):
        """add-secure-apps/flows-stages/stages/deny"""
        self.assertParity(
            """pending_user = request.context.get("pending_user")
return bool(pending_user and pending_user.pk and not pending_user.is_active)""",
            group("all", cond("user.id", "is_set"), cond("user.is_active", "is_false")),
            [
                Scenario("active"),
                Scenario("inactive", user=create_test_user(is_active=False)),
            ],
            [False, True],
        )

    def test_docs_password_skip_webauthn(self):
        """add-secure-apps/flows-stages/stages/password"""
        self.assertParity(
            """from authentik.stages.authenticator_webauthn.models import WebAuthnDevice

pending_user = request.context.get("pending_user")
if not pending_user:
    return True

return not WebAuthnDevice.objects.filter(user=pending_user, confirmed=True).exists()""",
            neg(cond("user.authenticator_types", "has_item", "webauthn")),
            [Scenario("no webauthn")],
            [True],
        )

    def test_docs_oauth_scope_group(self):
        """add-secure-apps/providers/oauth2"""
        admins = Group.objects.create(name=generate_id())
        member = create_test_user()
        member.groups.add(admins)
        self.assertParity(
            f"""if "my-admin-scope" in request.context["oauth_scopes"]:
    return ak_is_group_member(request.user, name="{admins.name}")
return True""",
            group(
                "any",
                neg(cond("oauth.scopes", "has_item", "my-admin-scope")),
                cond("user.groups", "has_item", str(admins.pk)),
            ),
            [
                Scenario("no admin scope", context={"oauth_scopes": {"openid"}}, in_flow=False),
                Scenario(
                    "admin scope, member",
                    user=member,
                    context={"oauth_scopes": {"openid", "my-admin-scope"}},
                    in_flow=False,
                ),
                Scenario(
                    "admin scope, not member",
                    context={"oauth_scopes": {"openid", "my-admin-scope"}},
                    in_flow=False,
                ),
            ],
            [True, True, False],
        )

    def test_docs_oauth_jwt_issuer(self):
        """add-secure-apps/providers/oauth2/machine_to_machine"""
        self.assertParity(
            'return request.context["oauth_jwt"]["iss"] == "https://my.issuer"',
            cond("oauth.jwt", "eq", "https://my.issuer", param="iss", cast="string"),
            [
                Scenario("match", context={"oauth_jwt": {"iss": "https://my.issuer"}}),
                Scenario("other", context={"oauth_jwt": {"iss": "https://other"}}),
            ],
            [True, False],
        )

    def test_docs_username(self):
        """customize/policies/types/expression"""
        marie = create_test_user(name="marie")
        self.assertParity(
            """if request.context["pending_user"].username == "marie":
    return True
return False""",
            cond("user.username", "eq", "marie"),
            [Scenario("marie", user=marie), Scenario("other")],
            [True, False],
        )

    def test_docs_geoip_asn(self):
        """customize/policies/types/expression/reference"""
        self.assertParity(
            'return context["geoip"]["continent"] == "EU" and context["asn"]["asn"] == 6939',
            group(
                "all",
                cond("request.geoip.continent", "eq", "EU"),
                cond("request.asn.asn", "eq", 6939),
            ),
            [
                Scenario("match", context={"geoip": {"continent": "EU"}, "asn": {"asn": 6939}}),
                Scenario("other", context={"geoip": {"continent": "NA"}, "asn": {"asn": 6939}}),
            ],
            [True, False],
        )

    def test_docs_unique_email(self):
        """customize/policies/types/expression/unique_email"""
        create_test_user(email="taken@goauthentik.io")
        self.assertParity(
            """field_name = "email"
email = request.context["prompt_data"][field_name]
pending_user = request.context.get("pending_user")

from authentik.core.models import User
query = User.objects.filter(email__iexact=email)
if pending_user:
    query = query.exclude(pk=pending_user.pk)
elif request.user and request.user.is_authenticated:
    query = query.exclude(pk=request.user.pk)

if query.exists():
    ak_message("Email address in use")
    return False

return True""",
            neg(cond("prompt_data.email_in_use", "is_true", param="email")),
            [
                Scenario("taken", context={"prompt_data": {"email": "TAKEN@goauthentik.io"}}),
                Scenario("free", context={"prompt_data": {"email": "free@goauthentik.io"}}),
            ],
            [False, True],
            failure_message="Email address in use",
        )

    def test_docs_email_domain_allowlist(self):
        """customize/policies/types/expression/whitelist_email"""
        allowed = create_test_user(email="foo@example.org")
        self.assertParity(
            """allowed_domains = ["example.org", "example.net", "example.com"]

current_domain = request.user.email.split("@")[1] if hasattr(request.user, 'email') and request.user.email else None
if current_domain in allowed_domains:
    return ak_is_sso_flow
else:
    ak_message("Authentication denied for this email domain")
    return False""",  # noqa: E501
            group(
                "all",
                cond(
                    "user.email",
                    "matches",
                    r"@(example\.org|example\.net|example\.com)$",
                ),
                cond("plan.is_sso", "is_true"),
            ),
            [
                Scenario("allowed, sso", user=allowed, context={"is_sso": True}),
                Scenario("allowed, not sso", user=allowed),
                Scenario("denied"),
            ],
            [True, False, False],
            # The expression only shows a message when the domain is not allowed
            compare_messages=False,
            failure_message="Authentication denied for this email domain",
        )

    def test_docs_notification_unknown_device(self):
        """sys-mgmt/events/notification_rule_expression_policies"""

        def event_scenario(name: str, action: str, known_device: bool):
            event = Event.new(action, auth_method_args={"known_device": known_device})
            return Scenario(name, context={"event": event}, in_flow=False)

        self.assertParity(
            """event = request.context.get("event")
if not event:
    return False
if event.action != "login":
    return False
known_device = event.context.get("auth_method_args", {}).get("known_device")
if known_device is False:
    return True
return False""",
            group(
                "all",
                cond("event.action", "eq", EventAction.LOGIN),
                cond(
                    "event.context",
                    "is_false",
                    param="auth_method_args.known_device",
                    cast="boolean",
                ),
            ),
            [
                event_scenario("unknown device", EventAction.LOGIN, False),
                event_scenario("known device", EventAction.LOGIN, True),
                event_scenario("other action", EventAction.LOGOUT, False),
            ],
            [True, False, False],
            missing_behavior=MissingBehavior.FALSE,
        )

    def test_docs_notification_client_ip(self):
        """sys-mgmt/events/notifications"""

        def event_scenario(name: str, client_ip: str):
            event = Event.new(EventAction.LOGIN)
            event.client_ip = client_ip
            return Scenario(name, context={"event": event}, in_flow=False)

        self.assertParity(
            """if "event" not in request.context:
    return False

return ip_address(request.context["event"].client_ip) in ip_network('192.0.2.0/24')""",
            cond("event.client_ip", "in_network", ["192.0.2.0/24"]),
            [event_scenario("inside", "192.0.2.4"), event_scenario("outside", "10.0.0.1")],
            [True, False],
        )

    def test_docs_invitation(self):
        """users-sources/user/invitations"""
        self.assertParity(
            "return context.get('invitation_in_effect', False)",
            cond("invitation.in_effect", "is_true"),
            [Scenario("invited", context={"invitation_in_effect": True}), Scenario("not invited")],
            [True, False],
        )

    def test_docs_password_reset_on_login(self):
        """users-sources/user/password_reset_on_login"""
        reset = create_test_user(attributes={"reset_password": True})
        self.assertParity(
            """if request.context["pending_user"].attributes.get("reset_password") == True:
    return True
return False""",
            cond("user.attributes", "is_true", param="reset_password", cast="boolean"),
            [Scenario("reset", user=reset), Scenario("no reset")],
            [True, False],
            missing_behavior=MissingBehavior.FALSE,
        )

    def test_docs_user_switching(self):
        """users-sources/user/user-switching"""
        self.assertParity(
            """flow_plan = request.context.get("flow_plan")
is_user_switch = bool(flow_plan and flow_plan.context.get("user_switch_from_user"))
return not is_user_switch""",
            neg(cond("plan.user_switch_active", "is_true")),
            [
                Scenario("switch", context={"user_switch_from_user": self.user}),
                Scenario("no switch"),
            ],
            [False, True],
        )

    def test_docs_not_authenticated(self):
        """add-secure-apps/flows-stages/flow/snippets"""
        from guardian.shortcuts import get_anonymous_user

        self.assertParity(
            "return not request.user.is_authenticated",
            cond("user.is_authenticated", "is_false"),
            [
                Scenario("anonymous", user=AnonymousUser(), in_flow=False),
                Scenario("guardian anonymous", user=get_anonymous_user(), in_flow=False),
                Scenario("user"),
            ],
            # The expression treats guardian's anonymous user as authenticated
            [True, None, False],
        )
        conditional = ConditionalPolicy(actions=tree(cond("user.is_authenticated", "is_false")))
        self.assertTrue(conditional.passes(PolicyRequest(get_anonymous_user())).passing)

    def test_docs_password_repeat(self):
        """add-secure-apps/flows-stages/stages/prompt"""
        node = cond(
            "prompt_data",
            "eq",
            param="password",
            cast="string",
        )
        node["value"] = var("prompt_data", param="password_repeat", cast="string")
        self.assertParity(
            """if request.context["prompt_data"]["password"] == request.context["prompt_data"]["password_repeat"]:
    return True

ak_message("Passwords don't match.")
return False""",  # noqa: E501
            node,
            [
                Scenario(
                    "match", context={"prompt_data": {"password": "a", "password_repeat": "a"}}
                ),
                Scenario(
                    "mismatch", context={"prompt_data": {"password": "a", "password_repeat": "b"}}
                ),
            ],
            [True, False],
            failure_message="Passwords don't match.",
        )

    def test_docs_group_membership_and_authenticator(self):
        """expressions/reference/_functions"""
        members = Group.objects.create(name=generate_id())
        member = create_test_user(username="some-admin")
        member.groups.add(members)
        TOTPDevice.objects.create(user=member, name="totp", confirmed=True)
        self.assertParity(
            f"""return (
    ak_is_group_member(request.user, name="{members.name}")
    and ak_user_has_authenticator(request.user)
    and regex_match(request.user.username, '.*admin.*')
)""",
            group(
                "all",
                cond("user.groups", "has_item", str(members.pk)),
                neg(cond("user.authenticator_types", "is_empty")),
                cond("user.username", "matches", ".*admin.*"),
            ),
            [Scenario("member", user=member), Scenario("not member")],
            [True, False],
        )

    def test_docs_call_policy(self):
        """expressions/reference/_functions"""
        referenced = ExpressionPolicy.objects.create(
            name=generate_id(), expression="return request.user.is_active"
        )
        self.assertParity(
            f'return ak_call_policy("{referenced.name}").passing',
            {"type": "policy", "policy": str(referenced.pk)},
            [Scenario("active"), Scenario("inactive", user=create_test_user(is_active=False))],
            [True, False],
        )


def set_action(key: str, value: dict, param: str | None = None) -> dict:
    return {"type": "set", "target": {"key": key, "param": param}, "value": value}


def literal(value) -> dict:
    return {"type": "literal", "value": value}


class TestExpressionParityActions(TestCase):
    """Expression policies which modify the flow, re-built with actions"""

    def setUp(self):
        self.user = create_test_user()

    def build_request(self, context: dict) -> PolicyRequest:
        plan = FlowPlan(flow_pk=generate_id())
        plan.context = context
        request = PolicyRequest(self.user)
        request.http_request = RequestFactory().get("/")
        request.context = {**context, "flow_plan": plan}
        return request

    def assertActionParity(  # noqa: N802
        self,
        expression: str,
        actions: list[dict],
        contexts: list[Callable[[], dict]],
        expected: list[bool],
        **kwargs,
    ):
        expression_policy = ExpressionPolicy(name=generate_id(), expression=expression)
        conditional = ConditionalPolicy(
            name=generate_id(), actions={"version": 2, "actions": actions}, **kwargs
        )
        for idx, (context, passing) in enumerate(zip(contexts, expected, strict=True)):
            with self.subTest(scenario=idx):
                expression_request = self.build_request(context())
                conditional_request = self.build_request(context())
                expression_result = expression_policy.passes(expression_request)
                conditional_result = conditional.passes(conditional_request)
                self.assertEqual(expression_result.passing, passing, "expression")
                self.assertEqual(conditional_result.passing, passing, "conditional")
                self.assertEqual(
                    list(expression_result.messages), list(conditional_result.messages)
                )
                self.assertEqual(
                    expression_request.context["flow_plan"].context,
                    conditional_request.context["flow_plan"].context,
                )

    def test_docs_consent_header(self):
        """add-secure-apps/flows-stages/stages/consent"""
        header = "Are you OK with your IdP provider sharing your user identification data?"
        self.assertActionParity(
            f"""request.context["flow_plan"].context["consent_header"] = "{header}"
return True""",
            [set_action("plan.consent_header", literal(header))],
            [dict],
            [True],
        )

    def test_docs_redirect_stage_target(self):
        """customize/policies/types/expression/managing_flow_context_keys"""
        self.assertActionParity(
            """context["flow_plan"].context["redirect_stage_target"] = "ak-flow://redirected-authentication-flow"
return True""",  # noqa: E501
            [
                set_action(
                    "plan.context",
                    literal("ak-flow://redirected-authentication-flow"),
                    param="redirect_stage_target",
                )
            ],
            [dict],
            [True],
        )

    def test_docs_email_override(self):
        """add-secure-apps/flows-stages/stages/email"""
        self.assertActionParity(
            """request.context["flow_plan"].context["email"] = request.context["prompt_data"]["email"]
return True""",  # noqa: E501
            [
                set_action(
                    "plan.email_override",
                    {
                        "type": "variable",
                        "variable": {"key": "prompt_data", "param": "email", "cast": "string"},
                    },
                )
            ],
            [lambda: {"prompt_data": {"email": "other@goauthentik.io"}}],
            [True],
        )

    def test_docs_google_username(self):
        """users-sources/sources/social-logins/google/cloud"""
        self.assertActionParity(
            """email = request.context["prompt_data"]["email"]
request.context["prompt_data"]["username"] = email
return False""",
            [
                set_action(
                    "prompt_data",
                    {
                        "type": "variable",
                        "variable": {"key": "prompt_data", "param": "email", "cast": "string"},
                    },
                    param="username",
                ),
                {"type": "stop", "result": "fail"},
            ],
            [lambda: {"prompt_data": {"email": "foo@goauthentik.io"}}],
            [False],
        )

    def test_docs_email_domain_enrollment(self):
        """customize/policies/types/expression/whitelist_email"""
        self.assertActionParity(
            """allowed_domains = ["example.org", "example.net", "example.com"]

current_domain = request.context["prompt_data"]["email"].split("@")[1] if request.context.get("prompt_data", {}).get("email") else None
if current_domain in allowed_domains:
    email = request.context["prompt_data"]["email"]
    request.context["prompt_data"]["username"] = email
    return ak_is_sso_flow
else:
    ak_message("Enrollment denied for this email domain")
    return False""",  # noqa: E501
            [
                {
                    "type": "if",
                    "condition": cond(
                        "prompt_data",
                        "matches",
                        r"@(example\.org|example\.net|example\.com)$",
                        param="email",
                        cast="string",
                    ),
                    "then_actions": [
                        set_action(
                            "prompt_data",
                            {
                                "type": "variable",
                                "variable": {
                                    "key": "prompt_data",
                                    "param": "email",
                                    "cast": "string",
                                },
                            },
                            param="username",
                        ),
                        {"type": "condition", "condition": cond("plan.is_sso", "is_true")},
                    ],
                    "else_actions": [
                        {
                            "type": "stop",
                            "result": "fail",
                            "message": "Enrollment denied for this email domain",
                        }
                    ],
                }
            ],
            [
                lambda: {"prompt_data": {"email": "foo@example.org"}, "is_sso": True},
                lambda: {"prompt_data": {"email": "foo@example.org"}},
                lambda: {"prompt_data": {"email": "foo@other.org"}, "is_sso": True},
            ],
            [True, False, False],
        )
