from dataclasses import dataclass

from authentik.core.models import User
from authentik.tenants.models import Tenant


@dataclass
class MockRequest:
    user: User
    query_params: dict[str, str]
    tenant: Tenant
