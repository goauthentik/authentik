"""passbook adapter"""
import requests
from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2CallbackView,
                                                          OAuth2LoginView)

from allauth_passbook.provider import PassbookProvider


class PassbookOAuth2Adapter(OAuth2Adapter):
    """passbook OAuth2 Adapter"""
    provider_id = PassbookProvider.id
    # pylint: disable=no-member
    settings = app_settings.PROVIDERS.get(provider_id, {}) # noqa
    provider_base_url = settings.get("PASSBOOK_URL", 'https://id.beryju.org')

    access_token_url = '{0}/application/oauth/token/'.format(provider_base_url)
    authorize_url = '{0}/application/oauth/authorize/'.format(provider_base_url)
    profile_url = '{0}/api/v1/openid/'.format(
        provider_base_url)

    def complete_login(self, request, app, access_token, **kwargs):
        headers = {
            'Authorization': 'Bearer {0}'.format(access_token.token),
            'Content-Type': 'application/json',
        }
        extra_data = requests.get(self.profile_url, headers=headers)

        return self.get_provider().sociallogin_from_response(
            request,
            extra_data.json()
        )


oauth2_login = OAuth2LoginView.adapter_view(PassbookOAuth2Adapter) # noqa
oauth2_callback = OAuth2CallbackView.adapter_view(PassbookOAuth2Adapter) # noqa
