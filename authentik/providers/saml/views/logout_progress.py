"""SAML Front-channel Logout Progress Tracking"""

import time
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class FrontChannelLogoutProgress:
    """Tracks progress through the front-channel logout redirect chain"""

    logout_id: str = field(default_factory=lambda: str(uuid4()))
    provider_ids: list[int] = field(default_factory=list)
    current_index: int = 0
    completed_providers: list[int] = field(default_factory=list)
    failed_providers: list[int] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize to dictionary for session storage"""
        return {
            "logout_id": self.logout_id,
            "provider_ids": self.provider_ids,
            "current_index": self.current_index,
            "completed_providers": self.completed_providers,
            "failed_providers": self.failed_providers,
            "start_time": self.start_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FrontChannelLogoutProgress":
        """Deserialize from dictionary"""
        return cls(
            logout_id=data.get("logout_id", str(uuid4())),
            provider_ids=data.get("provider_ids", []),
            current_index=data.get("current_index", 0),
            completed_providers=data.get("completed_providers", []),
            failed_providers=data.get("failed_providers", []),
            start_time=data.get("start_time", time.time()),
        )

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if logout process has exceeded timeout (default 5 minutes)"""
        return time.time() - self.start_time > timeout_seconds

    def get_next_provider_id(self) -> int | None:
        """Get the next provider ID to process"""
        if self.current_index < len(self.provider_ids):
            return self.provider_ids[self.current_index]
        return None

    def mark_current_completed(self, success: bool = True):
        """Mark the current provider as completed"""
        if self.current_index < len(self.provider_ids):
            provider_id = self.provider_ids[self.current_index]
            if success:
                self.completed_providers.append(provider_id)
            else:
                self.failed_providers.append(provider_id)
