"""Bounded server-side apply path for Agent-proposed Blueprints.

The authentik Agent proposes Blueprints, but a stored-instance apply bypasses the
caller's RBAC (applying a Blueprint is superuser-equivalent). The Agent therefore
never applies a Blueprint as the operator; a proposed Blueprint is applied as a
fixed least-privilege service account whose role only permits the models the
Agent may touch. That per-model, per-action RBAC is the server-side boundary
behind the Agent's client-side content validator, and it holds even when the
operator is a superuser.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from yaml import compose_all
from yaml.error import YAMLError
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from authentik.blueprints.v1.common import Blueprint, BlueprintEntryDesiredState
from authentik.core.models import User, UserTypes

# Username of the service account provisioned by
# blueprints/system/agent-apply-identity.yaml that Agent applies run as.
AGENT_APPLY_IDENTITY_USERNAME = "ak-agent-apply"

ALLOWED_MODELS = {
    "authentik_core.application": {
        "name",
        "slug",
        "group",
        "meta_launch_url",
        "meta_description",
        "meta_publisher",
        "meta_icon",
        "provider",
    },
    "authentik_providers_oauth2.oauth2provider": {
        "name",
        "client_type",
        "redirect_uris",
        "property_mappings",
        "authorization_flow",
        "invalidation_flow",
        "signing_key",
        "sub_mode",
        "issuer_mode",
        "include_claims_in_id_token",
        "access_code_validity",
        "access_token_validity",
    },
    "authentik_providers_saml.samlprovider": {
        "name",
        "acs_url",
        "audience",
        "sp_binding",
        "authorization_flow",
        "invalidation_flow",
        "signing_kp",
        "property_mappings",
    },
}
REFERENCE_FIELDS = {
    "provider",
    "property_mappings",
    "authorization_flow",
    "invalidation_flow",
    "signing_key",
    "signing_kp",
}
CURATED_SCOPES = {
    "goauthentik.io/providers/oauth2/scope-openid",
    "goauthentik.io/providers/oauth2/scope-email",
    "goauthentik.io/providers/oauth2/scope-profile",
    "goauthentik.io/providers/oauth2/scope-offline_access",
}
CURATED_FINDS = {
    ("authentik_providers_oauth2.scopemapping", "managed", scope) for scope in CURATED_SCOPES
} | {
    ("authentik_flows.flow", "slug", "default-provider-authorization-explicit-consent"),
    ("authentik_flows.flow", "slug", "default-provider-invalidation-flow"),
    ("authentik_crypto.certificatekeypair", "name", "authentik Self-signed Certificate"),
}
FIND_PARTS = 2
# Token-validity cap, mirroring the Agent's client-side validator (24h).
TOKEN_MAX_SECONDS = 60 * 60 * 24
# authentik timedelta units, in seconds — the vocabulary of a validity string
# like "hours=1;minutes=30".
_DURATION_UNITS = {
    "seconds": 1,
    "minutes": 60,
    "hours": 60 * 60,
    "days": 60 * 60 * 24,
    "weeks": 60 * 60 * 24 * 7,
}


def _mapping(node: Node | None) -> dict[str, Node]:
    if not isinstance(node, MappingNode):
        return {}
    return {
        key.value: value
        for key, value in node.value
        if isinstance(key, ScalarNode) and key.tag == "tag:yaml.org,2002:str"
    }


def _plain_scalar(node: Node | None) -> str | None:
    if not isinstance(node, ScalarNode) or node.tag != "tag:yaml.org,2002:str":
        return None
    return node.value


def _duration_seconds(node: Node | None) -> int | None:
    """Resolve a token-validity value to seconds, or None if unparseable.

    Accepts an integer (seconds) or an authentik timedelta string such as
    "hours=1;minutes=30". Any unknown unit or malformed part rejects the whole
    value (returns None), so the caller fails closed.
    """
    if not isinstance(node, ScalarNode):
        return None
    if node.tag == "tag:yaml.org,2002:int":
        try:
            return int(node.value)
        except ValueError:
            return None
    if node.tag != "tag:yaml.org,2002:str":
        return None
    text = node.value.strip()
    if text.isdigit():
        return int(text)
    total = 0
    parsed = False
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        unit, sep, amount = part.partition("=")
        if not sep or unit.strip() not in _DURATION_UNITS or not amount.strip().isdigit():
            return None
        total += int(amount.strip()) * _DURATION_UNITS[unit.strip()]
        parsed = True
    return total if parsed else None


def _check_reference(node: Node, entry_ids: set[str], errors: list[str]) -> None:
    if node.tag == "!KeyOf":
        target = _plain_scalar(node)
        if target not in entry_ids:
            errors.append("!KeyOf must reference an entry in this blueprint")
        return
    if node.tag != "!Find" or not isinstance(node, SequenceNode) or len(node.value) != FIND_PARTS:
        errors.append("references must be a curated !Find or an in-blueprint !KeyOf")
        return
    model = _plain_scalar(node.value[0])
    condition = node.value[1]
    if not isinstance(condition, SequenceNode) or len(condition.value) != FIND_PARTS:
        errors.append("!Find must have exactly one plain [field, value] condition")
        return
    field = _plain_scalar(condition.value[0])
    value = _plain_scalar(condition.value[1])
    if (model, field, value) not in CURATED_FINDS:
        errors.append("!Find reference is not a curated built-in")


def _check_tags(node: Node, entry_ids: set[str], errors: list[str]) -> None:
    if node.tag.startswith("!"):
        if node.tag not in {"!Find", "!KeyOf"}:
            errors.append(f"tag {node.tag!r} is not permitted")
            return
        _check_reference(node, entry_ids, errors)
        return
    if isinstance(node, MappingNode):
        for key, value in node.value:
            _check_tags(key, entry_ids, errors)
            _check_tags(value, entry_ids, errors)
    elif isinstance(node, SequenceNode):
        for value in node.value:
            _check_tags(value, entry_ids, errors)


def check_agent_apply_content(content: str) -> list[str]:
    """Return policy violations for content accepted by the bounded apply API."""
    try:
        documents = list(compose_all(content))
    except YAMLError as exc:
        return [f"Invalid YAML: {exc}"]
    if len(documents) != 1 or documents[0] is None:
        return ["Blueprint must contain exactly one YAML document"]
    root = documents[0]
    root_map = _mapping(root)
    entries = root_map.get("entries")
    if not isinstance(entries, SequenceNode):
        return ["Blueprint must contain an entries list"]

    entry_maps = [_mapping(entry) for entry in entries.value]
    entry_ids = {entry_id for entry in entry_maps if (entry_id := _plain_scalar(entry.get("id")))}
    errors: list[str] = []
    _check_tags(root, entry_ids, errors)

    for index, entry in enumerate(entry_maps):
        model = _plain_scalar(entry.get("model"))
        if model not in ALLOWED_MODELS:
            errors.append(f"entry {index}: model is not permitted")
            continue
        if "permissions" in entry:
            errors.append(f"entry {index}: permissions are not permitted")
        if "conditions" in entry:
            errors.append(f"entry {index}: conditions are not permitted")
        state = _plain_scalar(entry.get("state"))
        if state == "absent" or ("state" in entry and state is None):
            errors.append(f"entry {index}: state is not permitted")
        attrs = _mapping(entry.get("attrs"))
        if not attrs:
            errors.append(f"entry {index}: attrs must be a non-empty mapping")
            continue
        for name, value in attrs.items():
            if name not in ALLOWED_MODELS[model]:
                errors.append(f"entry {index}: attribute {name!r} is not permitted")
                continue
            if name in REFERENCE_FIELDS:
                values = [value]
                if isinstance(value, SequenceNode) and value.tag == "tag:yaml.org,2002:seq":
                    values = value.value
                if any(item.tag not in {"!Find", "!KeyOf"} for item in values):
                    errors.append(f"entry {index}: attribute {name!r} requires curated references")
        if model == "authentik_providers_oauth2.oauth2provider":
            if _plain_scalar(attrs.get("sub_mode")) not in {None, "hashed_user_id"}:
                errors.append(f"entry {index}: sub_mode must be hashed_user_id")
            if _plain_scalar(attrs.get("issuer_mode")) not in {None, "per_provider"}:
                errors.append(f"entry {index}: issuer_mode must be per_provider")
            claims = attrs.get("include_claims_in_id_token")
            if claims is not None and (
                claims.tag != "tag:yaml.org,2002:bool" or claims.value != "false"
            ):
                errors.append(f"entry {index}: include_claims_in_id_token must be false")
            for field in ("access_code_validity", "access_token_validity"):
                if (validity := attrs.get(field)) is None:
                    continue
                seconds = _duration_seconds(validity)
                if seconds is None or not 0 <= seconds <= TOKEN_MAX_SECONDS:
                    errors.append(
                        f"entry {index}: {field} must be a duration of at most "
                        f"{TOKEN_MAX_SECONDS} seconds"
                    )
    return errors


def get_agent_apply_identity() -> User | None:
    """The bounded service account Agent Blueprint applies run as, or None if it
    has not been provisioned."""
    return User.objects.filter(
        username=AGENT_APPLY_IDENTITY_USERNAME,
        type=UserTypes.INTERNAL_SERVICE_ACCOUNT,
    ).first()


def check_agent_apply_perms(blueprint: Blueprint, user: User) -> None:
    """Raise PermissionDenied unless `user` may apply every entry of `blueprint`.

    The desired state of each entry decides the required action: a present entry
    needs add + change, an absent entry needs delete. Because the bounded apply
    identity holds neither delete nor any permission outside the curated models,
    this refuses both out-of-scope models and destructive (delete) applies
    server-side, regardless of the operator's own privileges.
    """
    for entry in blueprint.iter_entries():
        full_model = entry.get_model(blueprint)
        app, __, model = full_model.partition(".")
        try:
            state = entry.get_state(blueprint)
        except ValueError:
            # An unresolvable/unknown state is treated as the most privileged
            # operation, so it is denied unless every action is held.
            required = [f"{app}.{action}_{model}" for action in ("add", "change", "delete")]
        else:
            if state == BlueprintEntryDesiredState.ABSENT:
                required = [f"{app}.delete_{model}"]
            else:
                required = [f"{app}.add_{model}", f"{app}.change_{model}"]
        for perm in required:
            if not user.has_perm(perm):
                raise PermissionDenied(
                    {
                        entry.id
                        or full_model: _(
                            "Agent apply identity lacks permission for {model}".format_map(
                                {"model": full_model}
                            )
                        )
                    }
                )
