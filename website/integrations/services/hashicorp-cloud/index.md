---
title: HashiCorp Cloud Platform
---

<span class="badge badge--secondary">Support level: Community</span>

## What is HashiCorp Cloud

> HashiCorp Cloud Platform is a fully managed platform for Terraform, Vault, Consul, and more.
>
> -- https://cloud.hashicorp.com/

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.

### Step 1 - HashiCorp Cloud

Login in under https://portal.cloud.hashicorp.com. Navigate to the _Settings_ entry in the sidebar, then _SSO_. Enable SSO and configure domain verification for the domain your users email have.

Under _Initiate SAML integration_, copy _SSO Sign-On URL_ and _Entity ID_.

### Step 2 - authentik

In authentik, under _Providers_, create a _SAML Provider_ with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: HashiCorp Cloud
-   ACS URL: _Value of **SSO Sign-On URL** from above_
-   Issuer: _Value of **Entity ID** from above_
-   Service Provider Binding: Post
-   Audience: _Value of **Entity ID** from above_

Open _Advanced protocol settings_, and ensure a signing certificate is selected, and all default property mappings are selected.

Create an application which uses this provider. Optionally apply access restrictions to the application using policy bindings.

-   Name: HashiCorp Cloud
-   Slug: hashicorp-cloud
-   Provider: HashiCorp Cloud

### Step 3 - HashiCorp Cloud

Open the Application's page in authentik and click on the provider name. Copy the value of _SSO URL (Redirect)_ and paste it into the _SAML IDP Single Sign-On URL_ field in the HashiCorp Cloud settings.

Download the certificate, open it in a text editor, and paste the contents into _SAML IDP Certificate_ in the HashiCorp Cloud settings.

Afterwards, logging in to HashiCorp Cloud with any email address ending in the domains verified above will redirect to your authentik instance, if those email addresses don't have an existing account.
