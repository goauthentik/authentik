---
title: Create an Entra ID provider
authentik_enterprise: true
---

For more information about using an Entra ID provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create an Entra ID provider in authentik, you must have already [configured Entra ID](./configure-entra.md).

## Create an Entra ID provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **Microsoft Entra Provider** as the provider type, then click **Next**.
4. On the **Create Microsoft Entra Provider** page, set the following configurations:
    - **Name**: provide a descriptive name (e.g. `Entra ID provider`)
    - Under **Protocol settings**:
        - **Client ID**: the Client ID that you copied when [configuring Entra ID](./configure-entra.md)
        - **Client Secret**: the secret from Entra ID
        - **Tenant ID**: the Tenant ID from Entra ID
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik
    - Under **User filtering**:
        - **Exclude service accounts**: choose whether to include or exclude service accounts
        - **Group**: select a group and only users within that group will be synced to Entra ID
    - Under **Attribute mapping**:
        - **User Property Mappings**: select any property mappings, or use the default
        - **Group Property Mappings**: select any property mappings, or use the default

        :::info Skipping certain users or groups
        The `SkipObject` exception can be used within a property mapping to prevent specific objects from being synced. Refer to the [Provider property mappings documentation](../property-mappings/index.md#skip-objects-during-synchronization) for more details.
        :::

5. Click **Finish**.

## Create an Entra ID application in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create**, and set the following configurations:
    - **Name**: provide a name for the application (e.g. `Entra ID`)
    - **Slug**: enter the name that you want to appear in the URL
    - **Provider**: this field should be left empty
    - **Backchannel Providers**: this field is required for Entra ID. Select the name of the Entra ID provider that you created in the previous section.
    - **UI settings**: leave these fields empty for Entra ID.

3. Click **Create**.

## Email handling (_optional_) {#email-handling}

When the default `authentik default Microsoft Entra Mapping: User` property mapping is used, authentik checks whether each user's email domain is verified in your Entra ID tenant.

In which case you must configure each user's email domain as a [verified custom domain in Entra ID](https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization); otherwise, provisioning fails. The tenant's default onmicrosoft.com domain (e.g., `@<tenant name>.onmicrosoft.com`), is considered a verified domain.

### Email-verified-users

Alternatively, if you need to provision users with email domains that you don't control, you can provision users as "email-verified-users" in Entra ID.

These are limited access accounts that must use email for verification when logging in, refer to the [Microsoft documentation](https://learn.microsoft.com/en-us/entra/identity/users/directory-self-service-signup) for more information about the limitations of these accounts.

This is possible via a modified property mapping:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **Microsoft Entra Provider Mapping** as the property mapping type and click **Next**.
4. Provide a **Name** for the property mapping and set the following **Expression**:

```python showLineNumbers
# Field reference: (note that keys have to converted to snake_case)
# https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.object_identity import ObjectIdentity

# Domains that are verified in Entra ID
verified_domains = {
    "company.com",
    "example.com",
    # add more domains here...
}

# Extract domain from email
email = request.user.email
domain = email.split("@", 1)[-1].lower()

if domain in verified_domains:
    # For users with verified domains
    user = {
        "display_name": request.user.name,
        "account_enabled": request.user.is_active,
        "mail_nickname": request.user.username,
        "user_principal_name": request.user.email,
    }
    if connection:
        # If there is a connection already made (discover or update), we can use
        # that connection's immutable_id...
        user["on_premises_immutable_id"] = connection.attributes.get("on_premises_immutable_id")
    else:
        user["password_profile"] = PasswordProfile(
            password=request.user.password
        )
        # ...otherwise we set an immutable ID based on the user's UID
        user["on_premises_immutable_id"] = request.user.uid
else:
    # For users with non-verified domains
    # e.g., email-verified-users
    # https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization
    user = {
        "display_name": request.user.name,
        "mail": request.user.email,
        "password_policies": "DisablePasswordExpiration", # this setting is required by Entra ID
        "user_type": "member" # can be set to "guest" to limit a user's access to read user lists
    }

    # for other sign in types
    # refer to https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    user["identities"] = [
        ObjectIdentity(
          sign_in_type = "federated",
          issuer = "mail",
          issuer_assigned_id = request.user.email,
        )
    ]

    user["password_profile"] = PasswordProfile(
        password=request.user.password
    )

return user
```

5. Click **Finish**.
6. Navigate to **Applications** > **Providers** and open the Entra ID provider that you previously created.
7. Under **Attribute mapping**, remove the `authentik default Microsoft Entra Mapping: User` property mapping and add the property mapping that you just created.
8. Click **Update**.
