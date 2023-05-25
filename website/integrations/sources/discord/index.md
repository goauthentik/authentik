---
title: Discord
---

<span class="badge badge--primary">Support level: authentik</span>

Allows users to authenticate using their Discord credentials

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.

## Discord

1. Create an application in the Discord Developer Portal (This is Free) https://discord.com/developers/applications

![New Application Button](discord1.png)

2. Name the Application

![Name App](discord2.png)

3. Select **OAuth2** from the left Menu

4. Copy the **Client ID** and _save it for later_

5. **Click to Reveal** the Client Secret and _save it for later_

6. Click **Add Redirect** and add https://authentik.company/source/oauth/callback/discord/

Here is an example of a completed OAuth2 screen for Discord.

![](discord3.png)

## authentik

8. Under _Directory -> Federation & Social login_ Click **Create Discord OAuth Source**

9. **Name:** Choose a name (For the example I used Discord)
10. **Slug:** discord (You can choose a different slug, if you do you will need to update the Discord redirect URLand point it to the correct slug.)
11. **Consumer Key:** Client ID from step 4
12. **Consumer Secret:** Client Secret from step 5

Here is an example of a complete authentik Discord OAuth Source

![](discord4.png)

Save, and you now have Discord as a source.

:::note
For more details on how-to have the new source display on the Login Page see [here](../general#add-sources-to-default-login-page).
:::

### Checking for membership of a Discord Guild

:::info
Ensure that the Discord OAuth source in 'Federation & Social login' has the additional `guilds` scope added under the 'Protocol settings'.
:::

Create a new 'Expression Policy' with the content below, adjusting the variables where required:

```python
# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."

# Only change below here if you know what you are doing.

# Ensure flow is only run during OAuth logins via Discord
if context['source'].provider_type != "discord":
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

Now bind this policy to the chosen enrollment and authentication flows for the Discord OAuth source.

### Checking for membership of a Discord Guild role

:::info
Ensure that the Discord OAuth source in 'Federation & Social login' has the additional `guilds guilds.members.read` scopes added under the 'Protocol settings'.
:::

Create a new 'Expression Policy' with the content below, adjusting the variables where required:

```python
# To get the role and guild ID numbers for the parameters, open Discord, go to Settings > Advanced and
# enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.
# Right-click on the server/guild title and select server settings > roles, right click on the role and click
# "Copy ID" to get the role ID.

ACCEPTED_ROLE_ID = "123456789123456789"
ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."
ROLE_NAME_STRING = "The desired role name in the error message."

# Only change below here if you know what you are doing.
GUILD_API_URL = f"https://discord.com/api/users/@me/guilds/{ACCEPTED_GUILD_ID}/member"

# Ensure flow is only run during OAuth logins via Discord
if context['source'].provider_type != "discord":
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

Now bind this policy to the chosen enrollment and authentication flows for the Discord OAuth source.

### Syncing discord roles to authentik groups

:::info
Ensure that the Discord OAuth source in 'Federation & Social login' has the additional `guilds.members.read` scopes added under the 'Protocol settings'.
:::

Create a new 'Expression Policy' with the content below, adjusting the variables where required:

#### Sync on enrollment

```python
# To get the role and guild ID numbers for the parameters, open Discord, go to Settings > Advanced and
# enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.
# Right-click on the server/guild title and select server settings > roles, right click on the role and click
# "Copy ID" to get the role ID.

from authentik.core.models import Group

GUILD_ID = "<YOUR GUILD ID>"
MAPPED_ROLES = {
  "<Discord Role Id>": Group.objects.get_or_create(name="<Authentik Role Name>")[0],
}

# Only change below here if you know what you are doing.
GUILD_API_URL = "https://discord.com/api/users/@me/guilds/{guild_id}/member"

# Ensure flow is only run during oatuh logins via Discord
if context['source'].provider_type != "discord":
  ak_message(f"Wrond provider: {context['source'].provider_type}")
  return False

# Get the user-source connection object from the context, and get the access token
connection = context['goauthentik.io/sources/connection']
access_token = connection.access_token

guild_member_info = requests.get(
  GUILD_API_URL.format(guild_id=GUILD_ID),
  headers={
    "Authorization": "Bearer " + access_token
  },
).json()

# Ensure user is a member of the guild
if "code" in guild_member_info:
    if guild_member_info['code'] == 10004:
        ak_message("User is not a member of the guild")
    else:
        ak_create_event("discord_error", source=context['source'], code=guild_member_info['code'])
        ak_message("Discord API error, try again later.")
    return False

# Add all mapped roles the user has in the guild
groups_to_add = []
for role_id in MAPPED_ROLES:
  if role_id in guild_member_info['roles']:
    groups_to_add.append(MAPPED_ROLES[role_id])

request.context["flow_plan"].context["groups"] = groups_to_add
return True
```

Now bind this policy to the chosen enrollment flows for the Discord OAuth source.

#### Sync on authentication

```python
# To get the role and guild ID numbers for the parameters, open Discord, go to Settings > Advanced and
# enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.
# Right-click on the server/guild title and select server settings > roles, right click on the role and click
# "Copy ID" to get the role ID.

from authentik.core.models import Group

GUILD_ID = "<YOUR GUILD ID>"
MAPPED_ROLES = {
  "<Discord Role Id>": Group.objects.get_or_create(name="<Authentik Role Name>")[0],
}

# Only change below here if you know what you are doing.
GUILD_API_URL = "https://discord.com/api/users/@me/guilds/{guild_id}/member"

# Ensure flow is only run during oatuh logins via Discord
if context['source'].provider_type != "discord":
  ak_message(f"Wrond provider: {context['source'].provider_type}")
  return False

# Get the user-source connection object from the context, and get the access token
connection = context['goauthentik.io/sources/connection']
access_token = connection.access_token

guild_member_info = requests.get(
  GUILD_API_URL.format(guild_id=GUILD_ID),
  headers={
    "Authorization": "Bearer " + access_token
  },
).json()

# Ensure user is a member of the guild
if "code" in guild_member_info:
    if guild_member_info['code'] == 10004:
        ak_message("User is not a member of the guild")
    else:
        ak_create_event("discord_error", source=context['source'], code=guild_member_info['code'])
        ak_message("Discord API error, try again later.")
    return False

# Get the user's current roles and remove all roles we want to remap
new_groups = [role for role in request.user.ak_groups.all() if role not in MAPPED_ROLES.values()]

# Add back mapped roles which the user has in the guild
for role_id in MAPPED_ROLES:
  if role_id in guild_member_info['roles']:
    new_groups.append(MAPPED_ROLES[role_id])

# Update user's groups
request.user.ak_groups.set(new_groups)
request.user.save()

return True
```

Now bind this policy to the chosen authentication flows for the Discord OAuth source.

### Store oauth info in attribute and create avatar attribute from discord avatar

:::info
Ensure that the Discord OAuth source in 'Federation & Social login' has the additional `guilds.members.read` scopes added under the 'Protocol settings'.
:::

:::info
In order to use the created attribute in authentik you will have to set authentik configuration arguments found at: https://goauthentik.io/docs/installation/configuration#authentik_avatars
:::

Create a new 'Expression Policy' with the content below, adjusting the variables where required:

```python
import base64
import requests

AVATAR_SIZE = "64" #Valid values: 16,32,64,128,256,512,1024

# Only change below here if you know what you are doing.
avatar_url = 'https://cdn.discordapp.com/avatars/{id}/{avatar}.png?site={avatar_size}'
avatar_stream_content = 'data:image/png;base64,{base64_string}' #Converts base64 image into html syntax useable with authentik's avatar attributes feature

def get_as_base64(url):
    """Returns the base64 content of the url
    """
    return base64.b64encode(requests.get(url).content)

def get_avatar_from_avatar_url(url):
    """Returns an authentik-avatar-attributes-compatible string from an image url
    """
    cut_url=f'{url}?size=64'
    return avatar_stream_content.format(base64_string=(get_as_base64(cut_url).decode("utf-8")))

user = request.user
userinfo = request.context['oauth_userinfo']

#Assigns the discord attributes to the user
user.attributes['discord'] = {
  'id': userinfo['id'],
  'username': userinfo['username'],
  'discriminator': userinfo['discriminator'],
  'email': userinfo['email'],
  'avatar': userinfo['avatar'],
  'avatar_url': avatar_url.format(id=userinfo['id'],avatar=userinfo['avatar'],avatar_size=AVATAR_SIZE) if userinfo['avatar'] else None,
}

#If the user has an avatar, assign it to the user
user.attributes['avatar'] = get_avatar_from_avatar_url(user.attributes['discord']['avatar_url'])
 
user.save()
return True
```

Now bind this policy to the chosen enrollment and authentication flows for the Discord OAuth source.