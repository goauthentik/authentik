---
title: Sources
---

Sources allow you to connect authentik to an external user directory. Sources can also be used with social login providers such as Facebook, Twitter, or GitHub.

### Find your source

Sources are in the following general categories:

- **Protocols** ([Kerberos](./protocols/kerberos/index.md), [LDAP](./protocols/ldap/index.md), [OAuth](./protocols/oauth/index.mdx), [SAML](./protocols/saml/index.md), and [SCIM](./protocols/scim/index.md))
- [**Property mappings**](./property-mappings/index.md) or how to import data from a source
- **Directory synchronization** (Active Directory, FreeIPA)
- **Social logins** (Apple, Discord, Twitch, Twitter, and many others)

For instructions to add a specific source, refer to the documentation links in the left navigation pane.

### Add Sources to Default Login Page

To have sources show on the default login screen you will need to add them to the flow. The process below assumes that you have not created or renamed the default stages and flows.

1. In the Admin interface, navigate to the **Flows** section.
2. Click on **default-authentication-flow**.
3. Click the **Stage Bindings** tab.
4. Chose **Edit Stage** for the _default-authentication-identification_ stage.
5. Under **Sources** you should see the additional sources that you have configured. Click all applicable sources to have them displayed on the Login page.
