from dataclasses import dataclass

from authentik.core.models import User


@dataclass
class MockRequest:
    user: User
    query_params: dict[str, str]
