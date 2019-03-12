"""passbook provider"""
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class PassbookAccount(ProviderAccount):
    """passbook account"""

    def to_str(self):
        dflt = super().to_str()
        return self.account.extra_data.get('username', dflt)


class PassbookProvider(OAuth2Provider):
    """passbook provider"""

    id = 'passbook'
    name = 'passbook'
    account_class = PassbookAccount

    def extract_uid(self, data):
        return str(data['sub'])

    def extract_common_fields(self, data):
        return {
            'email': data.get('email'),
            'username': data.get('preferred_username'),
            'name': data.get('name'),
        }

    def get_default_scope(self):
        return ['openid:userinfo']


provider_classes = [PassbookProvider] # noqa
