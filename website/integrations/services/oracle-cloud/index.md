---
title: Oracle Cloud
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Oracle Cloud

> Oracle Cloud is the first public cloud built from the ground up to be a better cloud for every application. By rethinking core engineering and systems design for cloud computing, we created innovations that accelerate migrations, deliver better reliability and performance for all applications, and offer the complete services customers need to build innovative cloud applications.
>
> -- https://www.oracle.com/cloud/

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.

### Step 1 - authentik

In authentik, under _Providers_, create an _OAuth2/OpenID Provider_ with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: Oracle Cloud
-   Client ID: Copy and Save this for Later
-   Client Secret: Copy and Save this for later
-   Signing Key: Select any available key

Create an application which uses this provider. Optionally apply access restrictions to the application using policy bindings.

-   Name: Oracle Cloud
-   Slug: oracle-cloud
-   Provider: Oracle Cloud

### Step 2 - Oracle Cloud

In Oracle Cloud, open the top-left navigation and go to _Identity & Security_ and then _Domains_. Click on the domain of your choice. Click on _Security_ in the sidebar, then on _Identity providers_.

Create a new _Social IdP_ via the _Add IdP_ button. Set the name to authentik and fill in the client ID and secret from above.

Set the _Discovery service URL_ to `https://authentik.company/application/o/oracle-cloud/.well-known/openid-configuration` and save the IdP. The IdP has now been created but must be enabled before it can be used to login with.

Navigate to _IdP Policies_ in the sidebar and open the default policy by clicking on it. Edit the first rule within the policy. Add authentik under _Assign identity providers_. Here you can optionally also remove username-based logins, however it is recommended to not remove the option until you've verified SSO works.
