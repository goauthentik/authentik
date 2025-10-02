---
title: Discord
support_level: authentik
---

Allows users to authenticate using their Discord credentials.

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
    - **Create Discord OAuth Source**: provide a name, a slug which must match the slug used in the Discord `Redirect URI`, and the following required configurations:
        - Under **Protocol Settings**:
            - **Consumer key**: Client ID from Discord.
            - **Consumer secret**: Client Secret from Discord
            - **Scopes**_(optional)_: if you need authentik to sync guild membership information from Disord, add the `guilds guilds.members.read` scope.

3. Click **Save**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

## Optional additional configuration

### Checking for membership of a Discord Guild

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
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

### Checking for membership of a Discord Guild role

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

To check if the user is member of a Discord Guild role, you can use the following policy on your flows:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
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

### Syncing Discord roles to authentik groups

:::info
Any authentik role that you want to sync with a Discord role needs to have the **attribute** `discord_role_id` with a value of the Discord role's ID set.
This setting can be found under `Authentik > Admin Interface > Directory > Groups > YOUR_GROUP > Attributes`
Example: `discord_role_id: "<ROLE ID>"`
:::

The following two policies allow you to synchronize roles in a Discord guild with roles in authentik.

Whenever a user enrolls or signs in to authentik via a Discord source, these policies will check the user's Discord roles and apply the user's authentik roles accordingly.

All roles with the attribute `discord_role_id` defined will be added or removed depending on whether the user is a member of the defined Discord role.

#### Sync on enrollment

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

The following policy will sync Discord roles when a user enrolls.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.core.models import Group

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

# Set these values
guild_id = "<YOUR GUILD ID>"
GUILD_API_URL = "https://discord.com/api/users/@me/guilds/{guild_id}/member"

# The following sections should not need to be edited
# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
    return False
access_token = connection.access_token

guild_member_request = requests.get(
    GUILD_API_URL.format(guild_id=guild_id),
    headers={
        "Authorization": f"Bearer {access_token}",
    },
)
guild_member_info = guild_member_request.json()

# Ensure we are not being ratelimited
if guild_member_request.status_code == 429:
    ak_message(f"Discord is throttling this connection. Retry in {int(guild_member_info['retry_after'])}s")
    return False

# Ensure user is a member of the guild
if "code" in guild_member_info:
    if guild_member_info["code"] == 10004:
        ak_message("User is not a member of the guild")
    else:
        ak_create_event("discord_error", source=context["source"], code=guild_member_info["code"])
        ak_message("Discord API error, try again later.")
    return False

# Get all discord_groups
discord_groups = Group.objects.filter(attributes__discord_role_id__isnull=False)

# Filter matching roles based on guild_member_info['roles']
user_groups_discord_updated = discord_groups.filter(attributes__discord_role_id__in=guild_member_info["roles"])

# Set matching_roles in flow context
request.context["flow_plan"].context["groups"] = user_groups_discord_updated

# Create event with roles added
ak_create_event(
    "discord_role_sync",
    user_discord_roles_added=", ".join(str(group) for group in user_groups_discord_updated),
)

return True

```

5. Click **Finish**. You can now bind this policy to the chosen enrollment flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the enrollment flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.

#### Sync on authentication

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

The following policy will sync Discord roles when a user logs in.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.core.models import Group

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

# Set these values
guild_id = "<YOUR GUILD ID>"
GUILD_API_URL = "https://discord.com/api/users/@me/guilds/{guild_id}/member"

# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
    return False
access_token = connection.access_token

guild_member_request = requests.get(
    GUILD_API_URL.format(guild_id=guild_id),
    headers={
        "Authorization": f"Bearer {access_token}"
    },
)
guild_member_info = guild_member_request.json()

# Ensure we are not being ratelimited
if guild_member_request.status_code == 429:
    ak_message(f"Discord is throttling this connection. Retry in {int(guild_member_info['retry_after'])}s")
    return False

# Ensure user is a member of the guild
if "code" in guild_member_info:
    if guild_member_info["code"] == 10004:
        ak_message("User is not a member of the guild")
    else:
        ak_create_event("discord_error", source=context["source"], code=guild_member_info["code"])
        ak_message("Discord API error, try again later.")
    return False

# Get all discord_groups
discord_groups = Group.objects.filter(attributes__discord_role_id__isnull=False)

# Split user groups into Discord groups and non Discord groups
user_groups_non_discord = request.user.ak_groups.exclude(pk__in=discord_groups.values_list("pk", flat=True))
user_groups_discord = list(request.user.ak_groups.filter(pk__in=discord_groups.values_list("pk", flat=True)))

# Filter matching roles based on guild_member_info['roles']
user_groups_discord_updated = discord_groups.filter(attributes__discord_role_id__in=guild_member_info["roles"])

# Combine user_groups_non_discord and matching_roles
user_groups_updated = user_groups_non_discord.union(user_groups_discord_updated)

# Update user's groups
request.user.ak_groups.set(user_groups_updated)

# Create event with roles changed
ak_create_event(
    "discord_role_sync",
    user_discord_roles_before=", ".join(str(group) for group in user_groups_discord),
    user_discord_roles_after=", ".join(str(group) for group in user_groups_discord_updated),
)

return True

```

5. Click **Finish**. You can now bind this policy to the chosen authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the authentication flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.

### Store OAuth info in attribute and create avatar attribute from Discord avatar

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

:::info
In order to use the created attribute in authentik you will have to set authentik configuration arguments found at: https://docs.goauthentik.io/docs/core/settings#avatars
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**.
3. Click **Create**, select **OAuth Source Property Mapping** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
import base64
import requests

AVATAR_SIZE = "64"  # Valid values: 16,32,64,128,256,512,1024. Larger values may cause HTTP error 431 on applications/providers due to headers being too large.
AVATAR_URL = "https://cdn.discordapp.com/avatars/{id}/{avatar}.png?size={avatar_size}"
AVATAR_STREAM_CONTENT = "data:image/png;base64,{base64_string}"  # Converts base64 image into html syntax usable with authentik's avatar attributes feature

def get_as_base64(url):
    """Returns the base64 content of the url"""
    return base64.b64encode(requests.get(url).content)

def get_avatar_from_avatar_url(url):
    """Returns an authentik-avatar-attributes-compatible string from an image url"""
    cut_url = f"{url}"
    return AVATAR_STREAM_CONTENT.format(
        base64_string=(get_as_base64(cut_url).decode("utf-8"))
    )

# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

user = request.user
userinfo = request.context["oauth_userinfo"]

# Assigns the Discord attributes to the user
user.attributes["discord"] = {
    "id": userinfo["id"],
    "username": userinfo["username"],
    "discriminator": userinfo["discriminator"],
    "email": userinfo["email"],
    "avatar": userinfo["avatar"],
    "avatar_url": (
        AVATAR_URL.format(
            id=userinfo["id"], avatar=userinfo["avatar"], avatar_size=AVATAR_SIZE
        )
        if userinfo["avatar"]
        else None
    ),
}

# If the user has an avatar, assign it to the user
avatar_url = user.attributes["discord"].get("avatar_url", None)
if avatar_url is not None:
    user.attributes["avatar"] = get_avatar_from_avatar_url(avatar_url)

user.save()
return True

```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Repeat the process for any other flows that you want the policy applied to.
