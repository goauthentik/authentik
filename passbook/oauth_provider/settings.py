"""passbook OAuth_Provider"""

CORS_ORIGIN_ALLOW_ALL = True
REQUEST_APPROVAL_PROMPT = 'auto'

MIDDLEWARE = [
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
]

OAUTH2_PROVIDER_APPLICATION_MODEL = 'passbook_oauth_provider.OAuth2Provider'

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {
        'openid:userinfo': 'Access OpenID Userinfo',
        # 'write': 'Write scope',
        # 'groups': 'Access to your groups'
    }
}
