"""Test Utils"""
from typing import Optional

from django.utils.text import slugify

from authentik.core.models import Group, User
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id


def create_test_flow(designation: FlowDesignation = FlowDesignation.STAGE_CONFIGURATION) -> Flow:
    """Generate a flow that can be used for testing"""
    uid = generate_id(10)
    return Flow.objects.create(
        name=uid,
        title=uid,
        slug=slugify(uid),
        designation=designation,
    )


def create_test_admin_user(name: Optional[str] = None) -> User:
    """Generate a test-admin user"""
    uid = generate_id(20) if not name else name
    group = Group.objects.create(name=uid, is_superuser=True)
    user = User.objects.create(
        username=uid,
        name=uid,
        email=f"{uid}@goauthentik.io",
    )
    group.users.add(user)
    return user
