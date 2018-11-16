"""passbook oauth_client Errors"""


class OAuthClientError(Exception):
    """Base error for all OAuth Client errors"""
    pass


class OAuthClientEmailMissingError(OAuthClientError):
    """Error which is raised when user is missing email address from profile"""
    pass
