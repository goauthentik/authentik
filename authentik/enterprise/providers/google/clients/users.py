from authentik.core.models import User
from authentik.enterprise.providers.google.clients.base import BaseGoogleSync
from authentik.enterprise.providers.google.models import GoogleProviderUser


class GoogleUserSync(BaseGoogleSync[User, "User"]):

    def convert_object(self, input: User) -> User:
        return super().convert_object(input)

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
