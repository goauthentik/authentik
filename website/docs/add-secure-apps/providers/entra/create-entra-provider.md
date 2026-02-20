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

## Email conversion (_optional_)

The Entra ID provider verifies whether the email domain of each user is available in Entra ID.

The email domain must be [configured as a custom email domain in Entra ID](https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization), otherwise user provisioning will fail.

Alternatively, users can be provisioned with the default onmicrosoft domain of the Entra ID tenant: `@<tenant name>.onmicrosoft.com`. A modified version of `authentik default Microsoft Entra Mapping: User` property mapping can be used to automatically convert any unavailable domains to the default onmicrosoft domain:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **Microsoft Entra Provider Mapping** as the property mapping type and click **Next**.
4. Provide a **Name** for the propert mapping and set the following **Expression**:

```python
# Field reference: (note that keys have to converted to snake_case)
# https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
from msgraph.generated.models.password_profile import PasswordProfile

email = request.user.email

if "@example.com" in email:  # replace with the domain you want to replace
    local_part = email.rsplit("@", 1)[0]
    updated_email = f"{local_part}@<tenant name>.onmicrosoft.com" # replace with the your tenant name you want to replace
else:
    updated_email = email

user = {
    "display_name": request.user.name,
    "account_enabled": request.user.is_active,
    "mail_nickname": request.user.name,
    "user_principal_name": updated_email,
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
return user
```
