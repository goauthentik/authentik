"""passbook prompt stage signals"""
from django.core.signals import Signal

# Arguments: password: str, plan_context: Dict[str, Any]
password_validate = Signal()
