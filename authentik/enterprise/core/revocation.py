"""Shared revocation of a user's active access.

The single place that removes everything granting a user access — their
authenticated sessions and every token-like credential. Account lockdown and
user offboarding both call it so the two features can never drift on what
"revoke this user's access" means.

Token models are discovered dynamically (any ``ExpiringModel`` tied to the user,
their session, or a provider), so new credential types are covered without
touching this module.
"""

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model, QuerySet
from django.db.transaction import atomic

from authentik.core.models import AuthenticatedSession, ExpiringModel, Session, Token, User


def _get_model_field(model: type[Model], field_name: str):
    """Get a model field by name, if present."""
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def _has_user_field(model: type[Model]) -> bool:
    """Check if a model has a direct user foreign key."""
    field = _get_model_field(model, "user")
    return bool(field and getattr(field, "remote_field", None) and field.remote_field.model is User)


def _has_authenticated_session_field(model: type[Model]) -> bool:
    """Check if a model is linked to an authenticated session."""
    field = _get_model_field(model, "session")
    return bool(
        field
        and getattr(field, "remote_field", None)
        and field.remote_field.model is AuthenticatedSession
    )


def _has_provider_field(model: type[Model]) -> bool:
    """Check if a model is linked to a provider."""
    return _get_model_field(model, "provider") is not None


def get_revocable_token_models() -> tuple[type[Model], ...]:
    """Return token, grant, and provider session models that revocation removes."""
    token_models: list[type[Model]] = []
    for model in apps.get_models():
        if model._meta.abstract or not issubclass(model, ExpiringModel):
            continue
        if model is Token:
            token_models.append(model)
        elif _has_user_field(model) and (
            _has_provider_field(model) or _has_authenticated_session_field(model)
        ):
            token_models.append(model)
        elif _has_authenticated_session_field(model):
            token_models.append(model)
    return tuple(token_models)


def get_revocable_token_queryset(model: type[Model], user: User) -> QuerySet:
    """Return the revocable artifacts of a single token model for a user."""
    manager = model.objects.including_expired()
    if _has_user_field(model):
        return manager.filter(user=user)
    return manager.filter(session__user=user)


def _revocable_querysets(user: User, *, sessions: bool, tokens: bool) -> tuple[QuerySet, ...]:
    """Return the querysets selected by the requested revocation."""
    querysets: list[QuerySet] = []
    if sessions:
        querysets.append(Session.objects.filter(authenticatedsession__user=user))
    if tokens:
        querysets.extend(
            get_revocable_token_queryset(model, user) for model in get_revocable_token_models()
        )
    return tuple(querysets)


def has_revocable_artifacts(user: User, *, sessions: bool = True, tokens: bool = True) -> bool:
    """Check whether the user still has sessions or tokens left to revoke."""
    return any(qs.exists() for qs in _revocable_querysets(user, sessions=sessions, tokens=tokens))


def revoke_user_access(user: User, *, sessions: bool = True, tokens: bool = True) -> None:
    """Delete the user's sessions and/or tokens, retrying until none remain.

    The retry loop guards a timing attack: a credential minted with a token
    that is being deleted in the same window. Callers that also deactivate the
    user should commit that first so no new valid credentials can be issued
    while the loop runs.
    """
    if not sessions and not tokens:
        return
    with atomic():
        for queryset in _revocable_querysets(user, sessions=sessions, tokens=tokens):
            queryset.delete()
    while has_revocable_artifacts(user, sessions=sessions, tokens=tokens):
        with atomic():
            for queryset in _revocable_querysets(user, sessions=sessions, tokens=tokens):
                queryset.delete()
