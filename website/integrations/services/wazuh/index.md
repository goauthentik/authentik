---
title: wazuh. 
---

<span class="badge badge--secondary">Support level: Community</span>

## What is wazuh

> wazuh is an open source Security Information and Event Management System that also has (extended) Endpoint Detection & Response (XDR) capabilities, as well as components of a Network Intrusion & Detection System (NIDS). 
>
> -- https://wazuh.com

:::note
We assume that you already have wazuh and authentik installed/setup and now want to integrate authentik as your IDP solution to have SSO within wazuh.
:::

## Preparation

The following placeholders will be used:

-   `wazuh.company` is the FQDN of the wazuh server instance.
-   `authentik.company` is the FQDN of the authentik install.

While wazuh allows both LDAP and SAML integration, in this post we will only walk through the SAML integration. 

### Step 1

The first step would be to add a certificate for wazuh.

You can generate a new one under `System` -> `Certificates` -> `Generate`


Add a name, set the validity period to 365 days and click `Generate`
![](./certificate.png)

If all goes well authentik will display a message like the one below
![](./certificate1.png)

### Step 2

Now add a SAML provider - you can find the options under `Applications` -> `Providers`

![](./provider.png)

Select SAML Provider and click Next
![](./provider1.png)

Add a descriptive name, select the appropriate Authentication/Authorization flow, adjust the ACS URL to contain the IP/hostname of your wazuh installation and add `/_opendistro/_security/saml/acs` to the end.

`https://<WAZUH_IP_OR_HOSTNAME>/_opendistro/_security/saml/acs`

also make sure to give it an appropriate `EntityID` name (`issuer`), you will need that later and a valid option is e.g. `wazuh-saml` 

Select `Post` as the `Service Provider Binding` and move on to the advanced protocol settings.
![](./provider2.png)

The last step is to select the previously created `Signing Certificate` from the dropdown list and leave the rest of the configurations as default for now. 
![](./provider3.png)
![](./provider4.png)
![](./provider5.png)

### Step 3

Time to create a Property Mapping - this is a custom function that takes group/user data from authentik and provides it to wazuh in a structured way. 

We will map a group membership - `wazuh-admins` - as a backend role for RBAC in wazuh using Property Mapping - `Customization` -> `Property Mappings`

`Name: wazuh property mapping`

`SAML Attribute Role: Roles`

![](./property-mapping.png)
![](./property-mapping2.png)

```python
if ak_is_group_member(request.user, name="wazuh-admins"):
  yield "wazuh-admin"
```

Make sure to adjust the provider to include the newly created property mapping in the `Advanced protocol settings`.
![](./property-mapping3.png)

### Step 4

Now create an application to use the newly created provider. `Applications` -> `Applications` - `Create`

`Name: wazuh`

`Slug: wazuh`

`Provider: SAML`

`Policy Engine: any`

![](./application.png)

### Step 5
