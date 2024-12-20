---
title: Browser configuration for SPNEGO
---

You might need to configure your web browser to allow SPNEGO. Following are the instructions for major browsers.

## Firefox

1.  In the address bar of Firefox, type `about:config` to display the list of current configuration options.
2.  In the **Filter** field, type `negotiate` to restrict the list of options.
3.  Double-click the `network.negotiate-auth.trusted-uris` entry to display the **Enter string value** dialog box.
4.  Enter the name of the domain against which you want to authenticate. For example, `.example.com`.

On Windows environments, to automate the deployment of this configuration use a [Group policy](https://support.mozilla.org/en-US/kb/customizing-firefox-using-group-policy-windows). On Linux or macOS systems, use [policies.json](https://support.mozilla.org/en-US/kb/customizing-firefox-using-policiesjson).

## Chrome

This section applies only for Chrome users on macOS and Linux machines. For Windows, see the instructions below.

1. Make sure you have the necessary directory created by running: `mkdir -p /etc/opt/chrome/policies/managed/`
2. Create a new `/etc/opt/chrome/policies/managed/mydomain.json` file with write privileges limited to the system administrator or root, and include the following line: `{ "AuthServerWhitelist": "*.example.com" }`.

**Note**: if using Chromium, use `/etc/chromium/policies/managed/` instead of `/etc/opt/chrome/policies/managed/`.

To automate the deployment of this configuration use a [Group policy](https://support.google.com/chrome/a/answer/187202).

## Windows / Internet Explorer

Log into the Windows machine using an account of your Kerberos realm (or administrative domain).

Open Internet Explorer, click **Tools** and then click **Internet Options**. You can also find **Internet Options** using the system search.

1. Click the **Security** tab.
2. Click **Local intranet**.
3. Click **Sites**.
4. Click **Advanced**.
5. Add your domain to the list.
6. Click the **Security tab**.
7. Click **Local intranet**.
8. Click **Custom Level**.
9. Select **Automatic login only in Intranet zone**.

To automate the deployment of this configuration use a [Group policy](https://learn.microsoft.com/en-us/previous-versions/troubleshoot/browsers/administration/how-to-configure-group-policy-preference-settings).
