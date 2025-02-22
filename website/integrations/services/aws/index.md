---
title: Integrate with Amazon Web Services
sidebar_label: Amazon Web Services
support_level: authentik
---

## What is AWS

> Amazon Web Services (AWS) is the world’s most comprehensive and broadly adopted cloud, with more than 200 fully featured services available from data centers globally. Millions of customers—including the fastest-growing startups, largest enterprises, and leading government agencies—are using AWS to lower costs, increase security, become more agile, and innovate faster.
>
> -- https://www.aboutamazon.com/what-we-do/amazon-web-services

## Select your method

There are two ways to perform the integration: the classic IAM SAML way, or the 'newer' IAM Identity Center way. This all depends on your preference and needs.

## Method 1: Classic IAM

### Preparation

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

- **ACS URL**: `https://signin.aws.amazon.com/saml`
- **Issuer**: `authentik`
- **Binding**: `Post`
- **Audience**: `urn:amazon:webservices`

You can use a custom signing certificate and adjust durations as needed.

### AWS

Create a role with the permissions you desire, and note the ARN.

After configuring the Property Mappings, add them to the SAML Provider in AWS.

Create an application, assign policies, and assign this provider.

Export the metadata from authentik and create a new Identity Provider [here](https://console.aws.amazon.com/iam/home#/providers).

#### Role Mapping

The Role mapping specifies the AWS ARN(s) of the identity provider, and the role the user should assume ([see](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml_assertions.html#saml_role-attribute)).

This Mapping needs to have the SAML Name field set to `https://aws.amazon.com/SAML/Attributes/Role`.

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

This mapping needs to have the SAML Name field set to `https://aws.amazon.com/SAML/Attributes/RoleSessionName`.

To use the user's username, use this snippet

```python
return user.username
```

## Method 2: IAM Identity Center

### Preparation

- A certificate to sign SAML assertions is required. You can use authentik's default certificate, or provide/generate one yourself.
- You may pre-create an AWS application.

### How to integrate with AWS

In AWS:

- In AWS, navigate to: **IAM Identity Center -> Settings -> Identity Source (tab)**
- On the right side, click **Actions** -> **Change identity source**
- Select **External Identity Provider**
- Under **Service Provider metadata** download the metadata file.

Now go to your authentik instance, and perform the following steps.

- Under **Providers**, create a new **SAML Provider from metadata**. Give it a name, and upload the metadata file AWS gave you.
- Click **Next**. Give it a name, and close the file.
- If you haven't done so yet, create an application for AWS and connect the provider to it.
- Navigate to the provider you've just created, and then select **Edit**
- Copy the **Issuer URL** to the **Audience** field.
- Under **Advanced Protocol Settings** set a **Signing Certificate**
- Save and Close.
- Under **Related Objects**, download the **Metadata file** and the **Signing Certificate**

Now go back to your AWS instance

- Under **Identity provider metadata**, upload both the **Metadata** file and **Signing Certificate** that authentik gave you.
- Click **Next**.
- In your settings pane, under the tab **Identity Source**, click **Actions** -> **Manage Authentication**.
- Note the AWS access portal sign-in URL (especially if you have customized it).

Now go back to your authentik instance.

- Navigate to the Application that you created for AWS and click **Edit**.
- Under **UI Settings** make sure the **Start URL** matches the **AWS access portal sign-in URL**.

:::::info

- Ensure users already exist in AWS for authentication through authentik. AWS will throw an error if the user is unrecognized.
- In case you're stuck, you can see the SSO logs in Amazon CloudTrail -> Event History. Look for `ExtenalIdPDirectoryLogin`.
  :::::

## Optional: Automated provisioning with SCIM

Some people may opt to use the automatic provisioning feature called SCIM (System for Cross-domain Identity Management).
SCIM allows you to synchronize (part of) your directory to AWS's IAM, saving you the hassle of having to create users by hand.
To do so, take the following steps in your AWS Identity Center:

- In your **Settings** pane, locate the **Automatic Provisioning** information box. Click **Enable**.
- AWS provides an SCIM Endpoint and an Access Token. Note these values.

Go back to your authentik instance

- Navigate to **Providers** -> **Create**
- Select **SCIM Provider**
- Give it a name, under **URL** enter the **SCIM Endpoint**, and then under **Token** enter the **Access Token** AWS provided you with.
- Optionally, change the user filtering settings to your liking. Click **Finish**

- Go to **Customization -> Property Mappings**
- Click **Create -> SCIM Mapping**
- Make sure to give the mapping a name that's lexically lower than `authentik default`, for example `AWS SCIM User mapping`
- As the expression, enter:

```python
# This expression strips the default mapping from its 'photos' attribute,
# which is a forbidden property in AWS IAM.
return {
    "photos": None,
}
```

- Click **Save**. Navigate back to your SCIM provider, click **Edit**
- Under **User Property Mappings** select the default mapping and the mapping that you just created.
- Click **Update**

- Navigate to your application, click **Edit**.
- Under **Backchannel providers** add the SCIM provider that you created.
- Click **Update**

The SCIM provider syncs automatically whenever you create/update/remove users, groups, or group membership. You can manually sync by going to your SCIM provider and clicking **Run sync again**. After the SCIM provider has synced, you should see the users and groups in your AWS IAM center.
