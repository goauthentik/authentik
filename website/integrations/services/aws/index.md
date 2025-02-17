---
title: Integrate with Amazon Web Services
sidebar_label: Amazon Web Services
---

# Integrate with Amazon Web Services

<span class="badge badge--primary">Support level: authentik</span>

## What is AWS

> Amazon Web Services (AWS) is the world’s most comprehensive and broadly adopted cloud, with more than 200 fully featured services available from data centers globally. Millions of customers—including the fastest-growing startups, largest enterprises, and leading government agencies—are using AWS to lower costs, increase security, become more agile, and innovate faster.
>
> -- https://www.aboutamazon.com/what-we-do/amazon-web-services

## Integration Methods

authentik supports two primary methods for AWS integration:

1. **Classic IAM (SAML)**: Traditional SAML-based authentication integration
2. **IAM Identity Center (AWS SSO)**: Modern, streamlined access management solution

## Method 1: Classic IAM (SAML Integration)

NEEDS NEW FORMAT

<!-- ### authentik Configuration

1. Create a new application in authentik
   - Note the application **slug** for later use

2. Set up a SAML provider with these settings:
   - ACS URL: `https://signin.aws.amazon.com/saml`
   - Issuer: `authentik`
   - Binding: `Post`
   - Audience: `urn:amazon:webservices`

3. Configure Property Mappings

#### Role Mapping Configuration

Set up role mapping by configuring the SAML Name field to `https://aws.amazon.com/SAML/Attributes/Role`. Choose one of these mapping approaches:

**Static ARN Mapping**:
```python
return "arn:aws:iam::123412341234:role/saml_role,arn:aws:iam::123412341234:saml-provider/authentik"
```

**Group-Based Role Mapping**:
```python
role_name = user.group_attributes().get("aws_role", "")
return f"arn:aws:iam::123412341234:role/{role_name},arn:aws:iam::123412341234:saml-provider/authentik"
```

**Multiple Role Mapping**:
```python
return [
    "arn:aws:iam::123412341234:role/role_a,arn:aws:iam::123412341234:saml-provider/authentik",
    "arn:aws:iam::123412341234:role/role_b,arn:aws:iam::123412341234:saml-provider/authentik",
    "arn:aws:iam::123412341234:role/role_c,arn:aws:iam::123412341234:saml-provider/authentik",
]
```

#### Session Name Configuration

Configure the RoleSessionName by setting the SAML Name field to `https://aws.amazon.com/SAML/Attributes/RoleSessionName`. To use the authenticated user's username:

```python
return user.username
``` -->

### AWS Configuration

1. Create an IAM Role

    - Navigate to the IAM console -- URL
    - Create a new role with appropriate permissions
    - Save the role's ARN for later use

2. Set up Identity Provider
    - Go to [IAM Providers](https://console.aws.amazon.com/iam/home#/providers)
    - Create a new provider using the authentik metadata
    - Follow the AWS console prompts to complete the setup

For additional details, consult the [AWS IAM Documentation on SAML](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml_assertions.html).

## Method 2: IAM Identity Center (AWS SSO)

NEEDS NEW FORMAT + SINCE ITS THE AWS METADATA IT SHOULD GO AFTER AWS CFG

<!-- ### authentik Configuration

1. Create SAML Provider
   - Navigate to **Providers** > **Create**
   - Select **SAML Provider from metadata**
   - Upload the AWS-provided metadata file

2. Configure Provider Settings
   - Set **Audience** to match AWS Issuer URL
   - Configure **Signing Certificate** in Advanced Protocol Settings
   - Download the **Metadata file** and **Signing Certificate** -->

### AWS Configuration

1. Set Identity Source

    - Access IAM Identity Center through AWS Console
    - Navigate to **Settings** > **Identity Source**
    - Select **Actions** > **Change identity source**
    - Choose **External Identity Provider**

2. Complete Provider Setup
    - Upload the authentik metadata file and signing certificate
    - Configure authentication settings
    - Note the AWS access portal URL

For more information, see the [AWS IAM Identity Center Documentation](https://docs.aws.amazon.com/singlesignon/latest/userguide/identity-source.html).

## SCIM Integration (Optional)

Enable automated user provisioning between authentik and AWS using SCIM.

NEEDS NEW FORMAT

<!-- ### authentik SCIM Setup

1. Create SCIM Provider
   - Go to **Providers** > **Create** > **SCIM Provider**
   - Configure with AWS SCIM endpoint and access token
   - Set desired user filtering options

2. Configure Property Mapping
   - Navigate to **Customization** > **Property Mappings**
   - Create new SCIM mapping
   - Use a name lexically preceding "authentik default" (e.g., "AWS SCIM User mapping")
   - Add the following expression:

```python
# Remove 'photos' attribute (not supported by AWS IAM)
return {
    "photos": None,
}
```

3. Update Provider Settings
   - Edit the SCIM provider
   - Add both the default and new mapping under User Property Mappings
   - Save changes -->

### AWS SCIM Setup

1. Enable Automatic Provisioning

    - Access Settings in AWS console
    - Enable SCIM provisioning
    - Save the provided endpoint and access token

2. Verify Configuration
    - Check user synchronization status
    - Test user provisioning
    - Monitor CloudTrail logs for any issues

### Important Notes

- Ensure users exist in AWS before attempting authentication
- SCIM sync occurs automatically for user/group changes
- Manual sync available through SCIM provider interface
- Monitor CloudTrail logs for troubleshooting (look for `ExternalIdPDirectoryLogin` events)

## Verification

After completing the integration:

1. Test user login through authentik
2. Verify proper role assignment in AWS
3. Check SCIM synchronization if enabled
4. Monitor logs for any authentication issues
