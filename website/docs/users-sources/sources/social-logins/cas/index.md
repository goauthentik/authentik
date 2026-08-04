---
title: Log in with Apereo CAS
sidebar_label: Apereo CAS
description: "Integrate Apereo CAS as a source in authentik"
tags: [source, cas, Apereo CAS, Apereo]
---

This source lets users authenticate with their Apereo CAS credentials by configuring CAS as a federated identity provider with OpenID Connect.

:::info
authentik does not support the native CAS protocol as a source. This guide uses the OpenID Connect provider that CAS ships in its `cas-server-support-oidc` module, so your CAS deployment must include that module.
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `cas.company` is the FQDN of the CAS installation.
- `cas-slug` is the slug to assign to the OAuth source in authentik (for example, `cas`).

This guide assumes CAS is served under the default `/cas` context path, so its OpenID Connect endpoints are below `https://cas.company/cas/oidc/`.

## CAS configuration

### Enable the OpenID Connect provider

Add the following to your CAS configuration, typically `/etc/cas/config/cas.properties`.

```properties title="/etc/cas/config/cas.properties"
cas.authn.oidc.core.issuer=https://cas.company/cas/oidc
# CAS generates this keystore on first start if it does not already exist.
cas.authn.oidc.jwks.file-system.jwks-file=file:/etc/cas/oidc/keystore.jwks

# Required for authentik. See the note below.
cas.authn.oauth.core.user-profile-view-type=FLAT
```

:::caution User profile view type
`cas.authn.oauth.core.user-profile-view-type` defaults to `NESTED`, which wraps every claim in an `attributes` object:

```json
{ "sub": "casuser", "attributes": { "email": "casuser@company", "name": "CAS User" } }
```

authentik reads claims from the top level of the user info response, so with the default it finds only `sub`, and users are enrolled with an empty email and name. Setting the value to `FLAT` emits the claims where authentik expects them.
:::

### Release attributes to authentik

CAS only sends the claims that a service is explicitly allowed to receive, and it can only send attributes that the principal actually has. If your CAS deployment resolves users from LDAP or a database, make sure the attributes you want are resolved under the names of the OpenID Connect claims that carry them: `email` for the `email` scope, and `name` and `preferred_username` for the `profile` scope.

For a test deployment that uses the static account handler, you can define the attributes directly:

```properties title="/etc/cas/config/cas.properties"
cas.authn.attribute-repository.stub.attributes.name=CAS Demo User
cas.authn.attribute-repository.stub.attributes.preferred_username=casuser
cas.authn.attribute-repository.stub.attributes.email=casuser@company
```

### Register authentik as a relying party

Create a JSON service definition in your CAS service registry directory, typically `/etc/cas/services`. The file name must be `<name>-<id>.json` and match the `name` and `id` fields inside it.

```json title="/etc/cas/services/authentik-1001.json"
{
    "@class": "org.apereo.cas.services.OidcRegisteredService",
    "clientId": "authentik",
    "clientSecret": "<a secret you generate>",
    "serviceId": "^https://authentik\\.company/source/oauth/callback/cas-slug/?.*",
    "name": "authentik",
    "id": 1001,
    "description": "authentik OAuth source delegating authentication to CAS",
    "bypassApprovalPrompt": true,
    "scopes": ["java.util.HashSet", ["openid", "profile", "email"]],
    "supportedResponseTypes": ["java.util.HashSet", ["code"]],
    "supportedGrantTypes": ["java.util.HashSet", ["authorization_code"]],
    "attributeReleasePolicy": {
        "@class": "org.apereo.cas.services.ChainingAttributeReleasePolicy",
        "policies": [
            "java.util.ArrayList",
            [
                { "@class": "org.apereo.cas.oidc.claims.OidcProfileScopeAttributeReleasePolicy" },
                { "@class": "org.apereo.cas.oidc.claims.OidcEmailScopeAttributeReleasePolicy" }
            ]
        ]
    }
}
```

`serviceId` is a regular expression that CAS matches against the callback URL, so the dots in the hostname are escaped and the slug must match the slug you give the source in authentik. Without `attributeReleasePolicy`, CAS authenticates the user but releases no claims beyond `sub`.

Restart CAS so it picks up the configuration and the new service definition.

## authentik configuration

To support the integration of CAS with authentik, you need to create an OpenID Connect OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **New Source**, and then configure the following settings:
    - **Select type**: select **OpenID Connect OAuth Source** as the source type.
    - **Create OpenID Connect OAuth Source**: provide a name, a slug that must match the slug used in the `serviceId` expression (for example, `cas`), and the following required settings:
        - Under **Protocol settings**:
            - **Consumer key**: enter the `clientId` from the CAS service definition.
            - **Consumer secret**: enter the `clientSecret` from the CAS service definition.
        - Under **URL settings**:
            - **OIDC Well-known URL**: `https://cas.company/cas/oidc/.well-known/openid-configuration`

3. Click **Finish** to save your settings.

authentik reads the authorization, token, user info, and JWKS URLs from the well-known URL, so you do not need to enter them individually.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Troubleshooting

- **Application Not Authorized to Use CAS**: CAS did not load a service definition matching the callback URL. Check that the `serviceId` expression matches `https://authentik.company/source/oauth/callback/<cas-slug>/`, that the file name matches the `name` and `id` fields, and that the JSON parses. A service file that fails to deserialize, for example because of a misspelled `@class` value, is skipped, and CAS reports this error as though the service were never registered.
- **Users are enrolled with an empty email and name**: CAS is returning nested claims. Set `cas.authn.oauth.core.user-profile-view-type` to `FLAT`.
- **Only `sub` is returned**: the service definition has no `attributeReleasePolicy`, or the principal has no attributes to release. Set `logging.level.org.apereo.cas.services=debug` in `cas.properties` and check the CAS log for the "Final collection of attributes allowed are" entry, which shows what CAS resolved and released.

## Resources

- [Apereo CAS Docs — OpenID Connect Authentication](https://apereo.github.io/cas/development/authentication/OIDC-Authentication.html)
- [Apereo CAS Docs — Attribute Release Policies](https://apereo.github.io/cas/development/integration/Attribute-Release-Policies.html)
- [Apereo CAS Docs — JSON Service Registry](https://apereo.github.io/cas/development/services/JSON-Service-Management.html)
