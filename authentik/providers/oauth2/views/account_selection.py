"""Compatibility shims for OAuth account selection flow plans.

Older in-flight browser sessions can contain a pickled in-memory OAuth account
selection stage. Keep these names importable so those sessions can finish on
the generic account selection stage instead of failing during session decode.
"""

from authentik.stages.account_selection.stage import (
    AccountSelectionChallenge as OAuthAccountSelectionChallenge,
)
from authentik.stages.account_selection.stage import (
    AccountSelectionChallengeResponse as OAuthAccountSelectionChallengeResponse,
)
from authentik.stages.account_selection.stage import (
    AccountSelectionChallengeUser as OAuthAccountSelectionUser,
)
from authentik.stages.account_selection.stage import (
    AccountSelectionStageView as OAuthAccountSelectionStage,
)

__all__ = [
    "OAuthAccountSelectionChallenge",
    "OAuthAccountSelectionChallengeResponse",
    "OAuthAccountSelectionStage",
    "OAuthAccountSelectionUser",
]
