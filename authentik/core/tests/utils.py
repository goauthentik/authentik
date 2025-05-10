"""Test Utils"""

from django.utils.text import slugify

from authentik.brands.models import Brand
from authentik.core.models import Group, User
from authentik.crypto.builder import CertificateBuilder, PrivateKeyAlg
from authentik.crypto.generators import generate_id
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation


def create_test_flow(
    designation: FlowDesignation = FlowDesignation.STAGE_CONFIGURATION, **kwargs
) -> Flow:
    """Generate a flow that can be used for testing"""
    uid = generate_id(10)
    return Flow.objects.create(
        name=uid, title=uid, slug=slugify(uid), designation=designation, **kwargs
    )


def create_test_user(name: str | None = None, **kwargs) -> User:
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


def create_test_admin_user(name: str | None = None, **kwargs) -> User:
    """Generate a test-admin user"""
    user = create_test_user(name, **kwargs)
    group = Group.objects.create(name=user.name or name, is_superuser=True)
    group.users.add(user)
    return user


def create_test_brand(**kwargs) -> Brand:
    """Generate a test brand, removing all other brands to make sure this one
    matches."""
    uid = generate_id(20)
    Brand.objects.all().delete()
    return Brand.objects.create(domain=uid, default=True, **kwargs)


def create_test_cert(alg=PrivateKeyAlg.RSA) -> CertificateKeyPair:
    """Generate a certificate for testing"""
    builder = CertificateBuilder(f"{generate_id()}.self-signed.goauthentik.io")
    builder.alg = alg
    builder.build(
        subject_alt_names=[f"{generate_id()}.self-signed.goauthentik.io"],
        validity_days=360,
    )
    builder.common_name = generate_id()
    return builder.save()
