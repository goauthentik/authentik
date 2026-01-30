"""API URLs"""

from authentik.enterprise.stages.account_lockdown.api import AccountLockdownStageViewSet

api_urlpatterns = [("stages/account_lockdown", AccountLockdownStageViewSet)]
