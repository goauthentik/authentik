---
title: Amazon Web Services
---

<span class="badge badge--primary">Support level: authentik</span>

## What is AWS

> Amazon Web Services (AWS) is the world’s most comprehensive and broadly adopted cloud, with more than 200 fully featured services available from data centers globally. Millions of customers—including the fastest-growing startups, largest enterprises, and leading government agencies—are using AWS to lower costs, increase security, become more agile, and innovate faster.
>
> -- https://www.aboutamazon.com/what-we-do/amazon-web-

## Select your method

There are two ways to perform the integration. The classic IAM SAML way, or the 'newer' IAM Identity Center way.
This all depends on your preference and needs.

# Method 1: Classic IAM

## Preparation

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

-   ACS URL: `https://signin.aws.amazon.com/saml`
-   Issuer: `authentik`
-   Binding: `Post`
-   Audience: `urn:amazon:webservices`

You can of course use a custom signing certificate, and adjust durations.

## AWS

Create a role with the permissions you desire, and note the ARN.

After you've created the Property Mappings below, add them to the Provider.

Create an application, assign policies, and assign this provider.

Export the metadata from authentik, and create an Identity Provider [here](https://console.aws.amazon.com/iam/home#/providers).

#### Role Mapping

The Role mapping specifies the AWS ARN(s) of the identity provider, and the role the user should assume ([see](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml_assertions.html#saml_role-attribute)).

This Mapping needs to have the SAML Name field set to "https://aws.amazon.com/SAML/Attributes/Role"

As expression, you can return a static ARN like so

```python
return "arn:aws:iam::123412341234:role/saml_role,arn:aws:iam::123412341234:saml-provider/authentik"
```

Or, if you want to assign AWS Roles based on Group membership, you can add a custom attribute to the Groups, for example "aws_role", and use this snippet below. Groups are sorted by name and later groups overwrite earlier groups' attributes.

```python
role_name = user.group_attributes().get("aws_role", "")
return f"arn:aws:iam::123412341234:role/{role_name},arn:aws:iam::123412341234:saml-provider/authentik"
```

If you want to allow a user to choose from multiple roles, use this snippet

```python
return [
    "arn:aws:iam::123412341234:role/role_a,arn:aws:iam::123412341234:saml-provider/authentik",
    "arn:aws:iam::123412341234:role/role_b,arn:aws:iam::123412341234:saml-provider/authentik",
    "arn:aws:iam::123412341234:role/role_c,arn:aws:iam::123412341234:saml-provider/authentik",
]
```

### RoleSessionName Mapping

The RoleSessionMapping specifies what identifier will be shown at the top of the Management Console ([see](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml_assertions.html#saml_role-session-attribute)).

This mapping needs to have the SAML Name field set to "https://aws.amazon.com/SAML/Attributes/RoleSessionName".

To use the user's username, use this snippet

```python
return user.username
```

# Method 2: IAM Identity Center

## Preparation

-   A certificate to sign SAML assertions is required. You can use authentik's default certificate, or provide/generate one yourself.
-   You may pre-create an AWS application.

## How to integrate with AWS

In AWS:

-   In AWS navigate to: _IAM Identity Center_ -> _Settings_ -> _Identity Source (tab)_
-   On the right side click _Actions_ -> _Change identity source_
-   Select _External Identity Provider_
-   Under _Service Provider metadata_ download the metadata file.

Now go to your authentik instance, and perform the following steps.

-   Under _Providers_ create a new _SAML Provider from metadata_. Give it a name, and upload the metadata file AWS gave you.
-   Click _Next_. Give it a name, and close the file.
-   If you haven't done so yet, create an application for AWS and connect the provider to it.
-   Navigate to the provider you've just created, and then select _Edit_
-   Copy the _Issuer URL_ to the _Audience_ field.
-   Under _Advanced Protocol Settings_ set a _Signing Certificate_
-   Save and Close.
-   Under _Related Objects_ download the _Metadata file_, and the _Signing Certificate_

Now go back to your AWS instance

-   Under _Identity provider metadata_ upload both the the _Metadata_ file and _Signing Certificate_ that authentik gave you.
-   Click _Next_.
-   In your settings pane, under the tab _Identity Source_, click _Actions_ -> _Manage Authentication_.
-   Take note of the _AWS access portal sign-in URL_ (this is especially important if you changed it from the default).

Now go back to your authentik instance.

-   Navigate to the Application that you created for AWS and click _Edit_.
-   Under _UI Settings_ make sure the _Start URL_ matches the _AWS access portal sign-in URL_

## Caveats and Troubleshooting

-   Users need to already exist in AWS in order to use them through authentik. AWS will throw an error if it doesn't recognise the user.
-   In case you're stuck, you can see the SSO logs in Amazon CloudTrail -> Event History. Look for `ExtenalIdPDirectoryLogin`

Note:

## Optional: Automated provisioning with SCIM

Some people may opt TO USE the automatic provisioning feature called SCIM (System for Cross-domain Identity Management).
SCIM allows you to synchronize (part of) your directory to AWS's IAM, saving you the hassle of having to create users by hand.
In order to do so, take the following steps in your AWS Identity Center:

-   In your _Settings_ pane, locate the _Automatic Provisioning_ information box. Click _Enable_.
-   AWS will give you an _SCIM Endpoint_ and a _Access Token_. Take note of these values.

Go back to your authentik instance

-   Navigate to _Providers_ -> _Create_
-   Select _SCIM Provider_
-   Give it a name, under _URL_ enter the _SCIM Endpoint_, and then under _Token_ enter the _Access Token_ AWS provided you with.
-   Optionally, change the user filtering settings to your liking. Click _Finish_

-   Go to _Customization -> Property Mappings_
-   Click _Create -> SCIM Mapping_
-   Make sure to give the mapping a name that's lexically lower than `authentik default`, for example `AWS SCIM User mapping`
-   As the expression, enter:

```python
# This expression strips the default mapping from its 'photos' attribute,
# which is a forbidden property in AWS IAM.
return {
    "photos": None,
}
```

-   Click _Save_. Navigate back to your SCIM provider, click _Edit_
-   Under _User Property Mappings_ select the default mapping and the mapping that you just created.
-   Click _Update_

-   Navigate to your application, click _Edit_.
-   Under _Backchannel providers_ add the SCIM provider that you created.
-   Click _Update_

The SCIM provider syncs automatically whenever you create/update/remove users, groups, or group membership. You can manually sync by going to your SCIM provider and clicking _Run sync again_. After the SCIM provider has synced, you should see the users and groups in your AWS IAM center.
