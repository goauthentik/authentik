# Machine-to-machine authentication

Client credentials can be used for machine-to-machine communication authentication. Clients can authenticate themselves using service-accounts; standard client_id + client_secret is not sufficient. This behavior is due to providers only being able to have a single secret at any given time.

Note that authentik does treat a grant type of `password` the same as `client_credentials` to support applications which rely on a password grant.

### Static authentication

Hence identification is based on service-accounts, and authentication is based on App-password tokens. These objects can be created in a single step using the _Create Service account_ function.

An example request can look like this:

```
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=application_client_id&
username=my-service-account&
password=my-token
```

This will return a JSON response with an `access_token`, which is a signed JWT token. This token can be sent along requests to other hosts, which can then validate the JWT based on the signing key configured in authentik.

### JWT-authentication

Starting with authentik 2022.4, you can authenticate and get a token using an existing JWT.

(For readability we will refer to the JWT issued by the external issuer/platform as input JWT, and the resulting JWT from authentik as the output JWT)

To configure this, the certificate used to sign the input JWT must be created in authentik. The certificate is enough, a private key is not required. Afterwards, configure the certificate in the OAuth2 provider settings under _Verification certificates_.

:::info
Starting with authentik 2022.6, you can define a JWKS URL/raw JWKS data in OAuth Sources, and use those to verify the key instead of having to manually create a certificate in authentik for them. This method is still supported but will be removed in a later version.
:::

With this configure, any JWT issued by the configured certificates can be used to authenticate:

```
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer&
client_assertion=$inputJWT&
client_id=application_client_id
```

Alternatively, you can set the `client_secret` parameter to the `$inputJWT`, for applications which can set the password from a file but not other parameters.

Input JWTs are checked to be signed by any of the selected _Verification certificates_, and their `exp` attribute must not be now or in the past.

To do additional checks, you can use _[Expression policies](../../policies/expression)_:

```python
return request.context["oauth_jwt"]["iss"] == "https://my.issuer"
```
