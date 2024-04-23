from typing import TYPE_CHECKING

from googleapiclient._apis.admin.directory_v1.schemas import User
from authentik.core.models import User
from authentik.enterprise.providers.google.clients.base import GoogleSyncClient
from authentik.enterprise.providers.google.models import GoogleProvider, GoogleProviderUser

if TYPE_CHECKING:
    from googleapiclient._apis.admin.directory_v1.resources import User as UserSchema


class GoogleUserSync(GoogleSyncClient[User, "UserSchema", GoogleProvider]):

    def to_schema(self, obj: User) -> "UserSchema":
        return super().to_schema(obj)

    def run(self):
        for user in User.objects.all():
            google_user = GoogleProviderUser.objects.filter(
                user=user, provider=self.provider
            ).first()
            if google_user:
                self.directory_service.users().update(userKey=google_user.id)
                continue
            created = (
                self.directory_service.users()
                .insert(
                    body={
                        "primaryEmail": user.email,
                        "name": {"givenName": "Elizabeth", "familyName": "Smith"},
                        "suspended": False,
                    }
                )
                .execute()
            )
            GoogleProviderUser.objects.create(
                user=user, provider=self.provider, id=created["primaryEmail"]
            )
