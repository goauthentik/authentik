from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class FlowState:

    flow_pk: Optional[UUID] = None
    pending_user_pk: int = -1
    factor_binding_last_order: int = -1
    user_authentication_backend: str = "django.contrib.auth.backends.ModelBackend"
