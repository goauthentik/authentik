---
title: NetBox
---

<span class="badge badge--secondary">Support level: Community</span>

## What is NetBox

From https://github.com/netbox-community/netbox

:::note
NetBox is the leading solution for modeling and documenting modern networks.
:::

## Preparation

The following placeholders will be used:

-   `netbox.company` is the FQDN of the NetBox install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to _Applications_ -> _Providers_. Create a _OAuth2/OpenID provider_ with the following parameters:

-   Client Type: `Confidential`
-   Redirect URIs: `https://netbox.company/oauth/complete/oidc/`
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key

Note the Client ID and Client Secret values. Create an application, using the provider you've created above.

## NetBox

:::info
This setup was tested and developed with NetBox Docker. For a non-Docker installation, the Docker part must be disabled and the non-docker part must be used.
:::

The following Docker env vars are required for the configuration.

```env
# Enable python-social-auth
REMOTE_AUTH_ENABLED='true'
REMOTE_AUTH_BACKEND='social_core.backends.open_id_connect.OpenIdConnectAuth'

# python-social-auth config
SOCIAL_AUTH_OIDC_ENDPOINT='https://authentik.company/application/o/<Application slug>/'
SOCIAL_AUTH_OIDC_KEY='<Client ID>'
SOCIAL_AUTH_OIDC_SECRET='<Client Secret>'
LOGOUT_REDIRECT_URL='https://authentik.company/application/o/<Application slug>/end-session/'
```

The Netbox configuration needs to be extended, for this you can create a new file in the configuration folder, for example `authentik.py`.

```py
from os import environ

#############
# Docker
#############

# python-social-auth configuration
SOCIAL_AUTH_OIDC_ENDPOINT = environ.get('SOCIAL_AUTH_OIDC_ENDPOINT')
SOCIAL_AUTH_OIDC_KEY = environ.get('SOCIAL_AUTH_OIDC_KEY')
SOCIAL_AUTH_OIDC_SECRET = environ.get('SOCIAL_AUTH_OIDC_SECRET')
LOGOUT_REDIRECT_URL = environ.get('LOGOUT_REDIRECT_URL')


#############
# non Docker
#############

# NetBox settings
#REMOTE_AUTH_ENABLED = True
#REMOTE_AUTH_BACKEND = 'social_core.backends.open_id_connect.OpenIdConnectAuth'

# python-social-auth configuration
#SOCIAL_AUTH_OIDC_ENDPOINT = 'https://authentik.company/application/o/<Application
#SOCIAL_AUTH_OIDC_KEY = '<Client ID>'
#SOCIAL_AUTH_OIDC_SECRET = '<Client Secret>'
#LOGOUT_REDIRECT_URL = 'https://authentik.company/application/o/<Application slug>/end-session/
```

### Groups

To manage groups in NetBox custom social auth pipelines are required. To create them you have to create the `custom_pipeline.py` file in the NetBox directory with the following content.

```python
from django.contrib.auth.models import Group

class AuthFailed(Exception):
    pass

def add_groups(response, user, backend, *args, **kwargs):
    try:
        groups = response['groups']
    except KeyError:
        pass

    # Add all groups from oAuth token
    for group in groups:
        group, created = Group.objects.get_or_create(name=group)
        group.user_set.add(user)

def remove_groups(response, user, backend, *args, **kwargs):
    try:
        groups = response['groups']
    except KeyError:
        # Remove all groups if no groups in oAuth token
        user.groups.clear()
        pass

    # Get all groups of user
    user_groups = [item.name for item in user.groups.all()]
    # Get groups of user which are not part of oAuth token
    delete_groups = list(set(user_groups) - set(groups))

    # Delete non oAuth token groups
    for delete_group in delete_groups:
        group = Group.objects.get(name=delete_group)
        group.user_set.remove(user)


def set_roles(response, user, backend, *args, **kwargs):
    # Remove Roles temporary
    user.is_superuser = False
    user.is_staff = False
    try:
        groups = response['groups']
    except KeyError:
        # When no groups are set
        # save the user without Roles
        user.save()
        pass

    # Set roles is role (superuser or staff) is in groups
    user.is_superuser = True if 'superusers' in groups else False
    user.is_staff = True if 'staff' in groups else False
    user.save()
```

The path of the file in the Official Docker image is: `/opt/netbox/netbox/netbox/custom_pipeline.py`

To enable the pipelines, add the pipelines section to the netbox configuration file from above

```python
SOCIAL_AUTH_PIPELINE = (
    ###################
    # Default pipelines
    ###################

    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. In some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social_core.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is where emails and domains whitelists are applied (if
    # defined).
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social_core.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social_core.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    # 'social_core.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social_core.pipeline.user.create_user',

    # Create the record that associates the social account with the user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social_core.pipeline.user.user_details',


    ###################
    # Custom pipelines
    ###################
    # Set authentik Groups
    'netbox.custom_pipeline.add_groups',
    'netbox.custom_pipeline.remove_groups',
    # Set Roles
    'netbox.custom_pipeline.set_roles'
)

```

### Roles

In netbox, there are two special user roles `superuser` and `staff`. To set them, add your users to the `superusers` or `staff` group in authentik.

To use custom group names, the following scope mapping example can be used. In the example, the group `netbox_admins` is used for the `superusers` and the group `netbox_staff` for the `staff` users.

Name: `Netbox roles`
Scope name: `roles`

Expression:

```python
return {
  "groups": ["superusers" if group.name == "netbox_admin" else "staff" if group.name == "netbox_staff" else group.name for group in request.user.ak_groups.all()],
}
```

This scope mapping must also be selected in the _OAuth2/OpenID Provider_ created above.
