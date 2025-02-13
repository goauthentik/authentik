---
title: Integrate with Plesk
sidebar_label: Plesk
---

# Integrate with Plesk

<span class="badge badge--secondary">Support level: Community</span>

## What is Plesk

> Plesk is a web hosting platform with a control panel that helps manage servers, applications, and websites through a comprehensive graphical user interface. It provides tools for web professionals, IT administrators, and hosting companies to simplify the process of hosting and managing websites.
>
> -- https://www.plesk.com

:::note
This documentation lists only the settings that you need to change from their default values. Changes other than those mentioned in this guide can cause issues accessing your application.
:::

:::caution
This integration works only with additional administrator accounts. It does not affect the main administrator account or customer accounts. The integration includes security measures such as strict token validation and secure OAuth implementation.
:::

## Preparation

Replace these placeholders in the guide with your values:

- _plesk.company_: The FQDN of your Plesk installation
- _authentik.company_: The FQDN of your authentik installation

## authentik configuration

1. In the Admin interface, navigate to **Applications** > **Providers** to create an OAuth2/OpenID provider with these settings:

    - **Name**: Plesk
    - **Redirect URI**: <kbd>https://<em>plesk.company</em>/modules/oauth/public/login.php</kbd>
    - **Signing Key**: Select any available key

2. Create an application using the provider:
    - Navigate to **Applications** > **Applications**
    - Create a new application and configure it to use the provider from step 1
    - Optionally, apply access restrictions to the application
    - Set the **Launch URL** to <kbd>https://<em>plesk.company</em></kbd>

## Plesk configuration

1. Install the OAuth login extension:

    - Log in to your Plesk installation
    - Navigate to **Extensions** in the left sidebar
    - Select **Extensions Catalog**
    - Search for "OAuth login"
    - Click **Install** next to the OAuth login extension

2. Enable and configure OAuth authentication:

    - After installation, select **Extensions** > **OAuth Login** in the left sidebar
    - Enable OAuth authentication using the toggle switch in the main configuration panel

3. In the same panel, configure these OAuth settings:

    - **Client ID**: Enter the Client ID from your authentik provider
    - **Client Secret**: Enter the Client Secret from your authentik provider
    - **Callback Host**: Enter your Plesk FQDN (example: <kbd>https://<em>plesk.company</em></kbd>)
    - **Authorize URL**: <kbd>https://<em>authentik.company</em>/application/o/authorize/</kbd>
    - **Token URL**: <kbd>https://<em>authentik.company</em>/application/o/token/</kbd>
    - **Userinfo URL**: <kbd>https://<em>authentik.company</em>/application/o/userinfo/</kbd>
    - **Scopes**: `openid,profile,email`
    - **Login Button Text**: Set your preferred text (example: "Log in with authentik")

    ![Plesk OAuth Login Settings](plesk-oauth-settings.png)

4. Click **Save** to apply the settings.

## Verify the configuration

To confirm that authentik is properly configured with Plesk:

1. Log out of Plesk
2. Look for the OAuth login button on the login page
3. Click the OAuth login button
4. Verify that you are redirected to authentik for authentication
5. After successful authentication, confirm that you can log in to your Plesk administrator account

![Plesk Login Page with OAuth Button](plesk-login-page.png)
