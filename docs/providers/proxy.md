# Proxy Provider

!!! info
    This provider is to be used in conjunction with [Outposts](../outposts/outposts.md)

This provider protects applications, which have no built-in support for OAuth2 or SAML. This is done by running a lightweight Reverse Proxy in front of the application, which authenticates the requests.

passbook Proxy is based on [oauth2_proxy](https://github.com/oauth2-proxy/oauth2-proxy), but has been integrated more tightly with passbook.

The Proxy these extra headers to the application:

Header Name | Value
-------------|-------
X-Auth-Request-User | The user's unique identifier
X-Auth-Request-Email | The user's email address
X-Auth-Request-Preferred-Username | The user's username
