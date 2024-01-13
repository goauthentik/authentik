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

## Alternative method: Federation using a SAML Provider from Metadata

When the Orancle Cloud tenancy does not have _Identity & Security_ menu does not have the _Domains_ entry but _Federation_, then this method will have to be used instead.

In contrast to the OpenID Method, you no OCI user is used or created for our the SAML logins, but the a Group Mapping is used instead.

Also Policies have to be created which allow the Federated users access. By default, tehy can log in, but cannot see or do anything.

Creating Policies has not been tested and is not described here.

See https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/federation.htm for more information.

### Federation Method, Step 1 - Oracle Cloud

In Oracle Cloud, open the top-left navigation and go to _Identity & Security_ and then _Federation_.

Below the list of active Identity Providers, you should see an information panel with this message:

> (i) You need the Oracle Cloud Infrastructure Federation Metadata document when setting up a trust with Microsoft Active Directory Federation Services or with other SAML 2.0-compliant identity providers. This is an XML document that describes Oracle Cloud Infrastructure endpoint and certificate information. __Download this document__ or Learn more.

Download the XML Document behind the link behind __Download this document__.

### Federation Method, Step 2 - authentik

In authentik, under _Providers_, create an _SAML Provider from Metadata_ with these settings:

-   Name: Oracle Cloud SAML <your tenancy> (or whatever you like as name for this provider)
-   Authorization flow: default-provider-authorization-explicit-consent (Authorize Application), implicit-consent may work too.
-   Metadata: Browse to the downloaded XML Document and 

Click Finish. Edit the Provider, below Protocol settings:

-   ACS URL: Copy this URL
-   Audicence: If empty, paste the ACS URL

Click Update. Click on the name of the new provider in the list to see the overview. Use the link _Create Application_ on this page to create the application for the provider.

Create an application which uses this provider. Optionally apply access restrictions to the application using policy bindings.

-   Name: Oracle Cloud SAML <your tenancy> (or whatever you like as name for this application)
-   Slug: oracle-cloud-saml-<your tenancy> (or whatever yoou like)
-   Group: You may want to enter a group name like Cloud-Admins (and create it) or use the Administriators group, note it for later.
-   Provider: Select the provider you created from the list.

Click Create. Back on the overview page page of the SAML provider, you show now see new information blocks.

The 2nd is titled __Related objects__ below the title, the label __Metadata__, and below it a __Download__ button. Download the Metadata using this button.

### Federation Method, Step 3 - Oracle Cloud

In Oracle Cloud, open the top-left navigation and go to _Identity & Security_ and then _Federation_.

In the title bar of the list of Identity Providers, you should see the button "Add Identity Provider"

Name: The name you enter here will be shown to the users when they select an Identity Provider from the list at long
Description: Whatever you like.
Type: SAML 2.0 Compliant Identity Provider
Upload the FederationMetadata.xml document from your Active Directory Federation Services server: Upload or drop the Metadata file downloaded from the authentik provider's Overview page.
Authentication Context Class References: Don't select any, as Authentik provides different references that are not listed here. If they do not match, the user gets an XML error showing both.

Click Continue

Here you’ll map groups defined in your Identity Provider to groups defined in Oracle Cloud Infrastructure (OCI). Each group can be mapped to one or more groups of the other kind.

Identity Provider Group: If you entered a Group for this provider in Authentik, you may have to use the same same Group here.
OCI Group: Select the OCI group to use for this Identity Provider Group in OCI.

Click the button _+ Add Another Mapping__ to add more user group mapping.

To log in, Users start from https://www.oracle.com/cloud/sign-in.html:
Cloud Accound Name: Name of the tenancy
Select your Identity Provider below: Select the name of the created Identity Provider from the list.
