---
title: Amazon Web Services
---

<span class="badge badge--primary">Support level: authentik</span>

## What is AWS

:::note
Amazon Web Services (AWS) is the world’s most comprehensive and broadly adopted cloud platform, offering over 175 fully featured services from data centers globally. Millions of customers—including the fastest-growing startups, largest enterprises, and leading government agencies—are using AWS to lower costs, become more agile, and innovate faster.
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.

Additional Preparation:
-   A certificate to sign SAML assertions is required. You can use Authentik's default certificate, or provide/generate one yourself.
-   You may pre-create an AWS application

## Procedure

In AWS:
-   In AWS Navigate to: `IAM Identity Center -> Settings -> Identity Source (tab)`
-   On the right hand side click `Actions -> Change identity source`
-   Select `External Identity Provider`
-   Under `Service Provider metadata` it'll allow you to download a metadata file. Download this file.

Now go to your authentik instance, and perform the following steps.
-   Under `Providers` create a new `SAML Provider from metadata`. Give it a name, and upload the metadata file AWS gave you.
-   Click `Next`. Give it a name, and close.
-   If you haven't done so yet, create an application for AWS and connect the Provider to it.
-   Navigate to the provider you've just created, select `Edit`
-   Copy the `Issuer` URL to the `Audience` field.
-   Under `Advanced Protocol Settings` set a `Signing Certificate`
-   Save and Close.
-   Under `Related Objects` download the `Metadata file`, and the `Signing Certificate`

Now go back to your AWS instance
-   Under `Identity provider metadata` upload both the the `Metadata file` and `Signing Certificate` authentik gave you.
-   Choose `Next`.
-   In your settings pane, under the tab `Identity Source` click `Actions -> Manage Authentication`
-   Take note of the `AWS access portal sign-in URL` (this is especially important if you've changed it from the default)

Now go back to your authentik instance.
-   Navigate to the Application you've created for AWS and click `Edit`.
-   Under `UI Settings` make sure the `Start URL` matches the `AWS access portal sign-in URL` 


## Caveats and Troubleshooting
-   Users need to exist in AWS in order to use them through authentik. AWS will throw an error if it doesn't recognise the user.
-   In case you're stuck, you can see the SSO logs in Amazon CloudTrail -> Event History. Look for `ExtenalIdPDirectoryLogin`


Note:

## Optional: Auto provisioning with SCIM
Some people may opt for the automatic provisioning feature called SCIM.
SCIM allows you to synchronise (part of) your directory to AWS's IAM. Saving you the hassle of having to create users by hand.
In order to do so, go to your AWS Identity Center

-   In your `Settings` pane, locate the `Automatic Provisioning` Info box. Click `Enable`
-   AWS will give you an `SCIM Endpoint` and a `Access Token`. Take note of these

Go back to your Authentik instance
-   Navigate to `Providers -> Create`
-   Select `SCIM Provider`
-   Give it a name, under `URL` enter the `SCIM Endpoint` and under `Token` enter the `Access Token` AWS provided you with.
-   In case you wish, change the user filtering settings to your liking. Click `Finish`
>   The next steps (regarding the Attribute Mapping) will become unneeded in a next release. At the time of writing `2023.5.0` it's a work-around for issue [#5640](https://github.com/goauthentik/authentik/issues/5640)
-   Go to `Customization -> Property Mappings`
-   Click `Create -> SCIM Mapping`
-   As the expression, enter: 
```python
        if " " in request.user.name:
            givenName, _, familyName = request.user.name.partition(" ")

        # photos supports URLs to images, however authentik might return data URIs
        avatar = request.user.avatar

        locale = request.user.locale()
        if locale == "":
            locale = None

        emails = []
        if request.user.email != "":
            emails.append({
                "value": request.user.email,
                "type": "other",
                "primary": True,
            })
        return {
            "userName": request.user.username,
            "name": {
                "formatted": request.user.name,
                "givenName": givenName,
                "familyName": familyName,
            },
            "displayName": request.user.name,
            "locale": locale,
            "active": request.user.is_active,
            "emails": emails,
        }
```

>    Note: The only thing this does, is strip the default mapping from it's 'photos' attribute, which is a forbidden property in AWS IAM.
-   Click `Save`. Navigate back to your SCIM provider, click `Edit`
-   Under `User Property Mappings` select _only_ the mapping you've just created.
-   Click `Update`
-   Navigate to your application, click `Edit`.
-   Under `Backchannel providers` add the SCIM provider you've created.
-   Click `Update`

The SCIM provider should sync automatically whenever you create/alter/remove anything.
You can manually sync by going to your SCIM provider and click the `Run sync again` button.
Once it synced, you should see the users and groups in your AWS IAM center.
