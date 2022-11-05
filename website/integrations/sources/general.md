---
title: General
slug: general
---

Sources allow you to connect authentik to an existing user directory. They can also be used for social logins, using external providers such as Facebook, Twitter, etc.

### Add Sources to Default Login Page

To have sources show on the default login screen you will need to add them. This is assuming you have not created or renamed the default stages and flows.

1. Access the **Flows** section

![image](https://user-images.githubusercontent.com/42992675/200095461-7fd0374e-3565-44fc-a50f-27a03e21c3b4.png)

2. Click on **default-authentication-flow**
3. Click the **Stage Bindings** tab
4. Chose **Edit Stage** for the _default-authentication-identification_ stage

![image](https://user-images.githubusercontent.com/42992675/200095484-6fe2e34d-6165-4c5a-87d5-fcfd463a8e04.png)

6. Under **Sources** you should see the additional sources you have configured. Click all applicable sources to have them displayed on the Login Page

![image](https://user-images.githubusercontent.com/42992675/200095514-15d81fca-d842-4f0f-b8d5-8341b661d198.png)
