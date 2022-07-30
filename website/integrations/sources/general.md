---
title: General
slug: general
---

Sources allow you to connect authentik to an existing user directory. They can also be used for social logins, using external providers such as Facebook, Twitter, etc.

### Add Sources to Default Login Page

To have sources show on the default login screen you will need to add them. This is assuming you have not created or renamed the default stages and flows.

1. Access the **Flows** section
2. Click on **default-authentication-flow**
3. Click the **Stage Bindings** tab
4. Chose **Edit Stage** for the _default-authentication-identification_ stage
5. Under **Sources** you should see the additional sources you have configured. Click all applicable sources to have them displayed on the Login Page
