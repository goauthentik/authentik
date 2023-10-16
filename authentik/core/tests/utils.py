"""Test Utils"""
from typing import Optional

from django.utils.text import slugify

from authentik.core.models import Group, User
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id
from authentik.tenants.models import Tenant


def create_test_flow(
    designation: FlowDesignation = FlowDesignation.STAGE_CONFIGURATION, **kwargs
) -> Flow:
    """Generate a flow that can be used for testing"""
    uid = generate_id(10)
    return Flow.objects.create(
        name=uid, title=uid, slug=slugify(uid), designation=designation, **kwargs
    )


def create_test_user(name: Optional[str] = None, **kwargs) -> User:
    """Generate a test user"""
    uid = generate_id(20) if not name else name
    kwargs.setdefault("email", f"{uid}@goauthentik.io")
    kwargs.setdefault("username", uid)
    user: User = User.objects.create(
        name=uid,
        **kwargs,
    )
    user.set_password(uid)
    user.save()
    return user


def create_test_admin_user(name: Optional[str] = None, **kwargs) -> User:
    """Generate a test-admin user"""
    user = create_test_user(name, **kwargs)
    group = Group.objects.create(name=user.name or name, is_superuser=True)
    group.users.add(user)
    return user


def create_test_tenant(**kwargs) -> Tenant:
    """Generate a test tenant, removing all other tenants to make sure this one
    matches."""
    uid = generate_id(20)
    Tenant.objects.all().delete()
    return Tenant.objects.create(domain=uid, default=True, **kwargs)


def create_test_cert(use_ec_private_key=False) -> CertificateKeyPair:
    """Generate a certificate for testing"""
    builder = CertificateBuilder(
        name=f"{generate_id()}.self-signed.goauthentik.io",
        use_ec_private_key=use_ec_private_key,
    )
    builder.build(
        subject_alt_names=[f"{generate_id()}.self-signed.goauthentik.io"],
        validity_days=360,
    )
    builder.common_name = generate_id()
    return builder.save()
