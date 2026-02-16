---
title: Discord
tags:
    - source
    - discord
---

Allows users to authenticate using their Discord credentials by configuring Discord as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Discord configuration

To integrate Discord with authentik you will need to create an OAuth application in the Discord Developer Portal.

1. Log in to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Navigate to **Applications** and click **New Application**.
3. Provide a name for the application, accept the terms, and then click **Create**.
4. Select **OAuth2** in the sidebar.
5. Under **Client Secret**, click **Reset Secret** and follow the steps.
6. Take note of the **Client ID** and **Client Secret**. They will be required in the next section.
7. Click **Add Redirect** and enter `https://authentik.company/source/oauth/callback/discord/`.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Discord OAuth Source** as the source type.
    - **Create Discord OAuth Source**: provide a name, a slug which must match the slug used in the Discord `Redirect URI` (e.g. `discord`), and the following required configurations:
        - Under **Protocol Settings**:
            - **Consumer key**: set the Client ID from Discord.
            - **Consumer secret**: set the Client Secret from Discord.
            - **Scopes** _(optional)_: if you need authentik to sync guild membership information from Disord, add the `guilds guilds.members.read` scope.

3. Click **Save**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Optional additional configuration

### Syncing Discord roles and avatars to authentik

The following property mapping allows you to synchronize roles from a Discord guild to roles in authentik.

Whenever a user enrolls in authentik via a Discord source, this property mapping will check the user's Discord roles and update the user's authentik groups accordingly.

:::info Group Attribute
Any authentik group that you want to sync with a Discord role needs to have a `discord_role_id` attribute set with the ID of the Discord role.
Example: `discord_role_id: "<ROLE ID>"`

This group attribute can be set via **Directory** > **Groups** > **Your_Group** > **Attributes**.
:::

:::info Required OAuth Scopes
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

:::info Avatar Setting
In order to use the created avatar attribute in authentik you will need to set the [authentik avatar configuration](../../../../sys-mgmt/settings.md#avatars).
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**.
3. Click **Create**, select **OAuth Source Property Mapping** and then **Next**.
4. Provide a name for the mapping and set the following expression:

```python
import base64
import requests
from authentik.core.models import Group

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

#Set these values
ACCEPTED_GUILD_ID = "123456789123456789" # Discord server id to fetch roles from
AVATAR_SIZE = "64" # Valid avatar size values: 16,32,64,128,256,512,1024.
# Larger values than 64 may cause HTTP error 431 on applications/providers
# due to headers being too large.

# Generate avatar URL and base64 avatar image
avatar_url = None
avatar_base64 = None

if info.get("avatar"):
    avatar_url = (f"https://cdn.discordapp.com/avatars/{info.get('id')}/"
                  f"{info.get('avatar')}.png?size={AVATAR_SIZE}")
    try:
        response = client.do_request("GET", avatar_url)
        encoded_image = base64.b64encode(response.content).decode('utf-8')
        avatar_base64 = f"data:image/png;base64,{encoded_image}"
    except:
        avatar_base64 = None

# Get guild membership
guild_url = f"https://discord.com/api/v10/users/@me/guilds/{ACCEPTED_GUILD_ID}/member"
guild_response = client.do_request("GET", guild_url, token=token)
guild_data = guild_response.json()

# Get matching groups
user_groups = Group.objects.filter(attributes__discord_role_id__in=guild_data["roles"])

# Return user data
return {
    "name": info.get("global_name"),
    "attributes.discord": {
        "id": info.get("id"),
        "username": info.get("username"),
        "discriminator": info.get("discriminator"),
        "email": info.get("email"),
        "avatar": info.get("avatar"),
        "avatar_url": avatar_url
    },
    "groups": [group.name for group in user_groups],
    "attributes.avatar": avatar_base64
}
```

5. Click **Finish**.
6. Navigate to **Directory** > **Federation and Social login** and click the **Edit** icon next to your Discord OAuth Source.
7. Under **OAuth Attribute mapping** add the newly create property mapping to **Selected User Property Mappings**.
8. Click **Update**.

### Checking Discord Guild membership

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.sources.oauth.models import OAuthSource

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

# Set these values
ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."

# The following sections should not need to be edited
# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
  return False
access_token = connection.access_token

guilds = requests.get(
    "https://discord.com/api/users/@me/guilds",
    headers= {
        "Authorization": f"Bearer {access_token}",
    }
).json()

user_matched = any(ACCEPTED_GUILD_ID == g["id"] for g in guilds)
if not user_matched:
    ak_message(f"User is not a member of {GUILD_NAME_STRING}.")
return user_matched
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and/or authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Optionally, repeat the process for any other flows that you want the policy applied to.

### Checking Discord Guild role membership

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

To check if the user is member of a Discord Guild role, you can use the following policy on your flows:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.sources.oauth.models import OAuthSource

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.
# Right-click on the server/guild title and select server settings > roles, right click on the role and click "Copy ID" to get the role ID.

#Set these values
ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."
ACCEPTED_ROLE_ID = "123456789123456789"
ROLE_NAME_STRING = "The desired role name in the error message."

GUILD_API_URL = f"https://discord.com/api/users/@me/guilds/{ACCEPTED_GUILD_ID}/member"

# The following sections should not need to be edited
# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
  return False
access_token = connection.access_token

guild_member_object = requests.get(
    GUILD_API_URL,
    headers= {
        "Authorization": f"Bearer {access_token}",
    }
).json()

# The response for JSON errors is held within guild_member_object['code']
# See: https://discord.com/developers/docs/topics/opcodes-and-status-codes#json
# If the user isn't in the queried guild, it gives the somewhat misleading code = 10004.
if "code" in guild_member_object:
    if guild_member_object['code'] == 10004:
        ak_message(f"User is not a member of {GUILD_NAME_STRING}.")
    else:
        ak_create_event("discord_error", source=context['source'], code=guild_member_object['code'])
        ak_message("Discord API error, try again later.")
    # Policy does not match if there is any error.
    return False

user_matched = any(ACCEPTED_ROLE_ID == g for g in guild_member_object["roles"])
if not user_matched:
    ak_message(f"User is not a member of the {ROLE_NAME_STRING} role in {GUILD_NAME_STRING}.")
return user_matched
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and/or authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Optionally, repeat the process for any other flows that you want the policy applied to.

## Resources

- [Discord Developer Documentation](https://discord.com/developers/docs/intro)
- [Discord Developer Documentation - OAuth2](https://discord.com/developers/docs/topics/oauth2#oauth2)
