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

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

-   ACS URL: `https://signin.aws.amazon.com/saml`
-   Audience: `urn:amazon:webservices`
-   Issuer: `authentik`
-   Binding: `Post`

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
