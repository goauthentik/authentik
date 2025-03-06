---
title: Facebook
support_level: community
---

Adding Facebook as a source allows users to authenticate through authentik using their Facebook credentials.

## Preparation

The following placeholders are used:

- `authentik.company` is the FQDN of the authentik installation.

## Facebook configuration

To integrate authentik with Facebook and access the user credentials from Facebook, you first need to register with Meta for Developers and create a developers account. Refer to the [Facebook documentation](https://developers.facebook.com/docs/development) for exact steps.

1. Visit https://developers.facebook.com/ and log in to your Facebook account.
2. After you log in, go to https://developers.facebook.com/async/registration and follow the steps to register as a developer.

Next, create an app so that Facebook generates a unique ID for your authentik app.

:::info
You will need the Facebook **App ID** and **App Secret** values from the Facebook app in order to configure the authentik integration. See Step 11. below for instructions.
:::

3. On the Meta for Developers Dashboard click **Create**.
4. Follow the prompts to create the app.

After you create the app you need to customize the login settings.

5. Go back to the Dashboard and in the left navigation pane click **Use Cases**.
6. On the **Use cases** page, click **Customize** under **Authentication and account creation**.
7. On the **Customize** page, click **Go to settings**.
8. On the **Facebook Login settings** page set the **Valid OAuth redirect URIs** field to `https://authentik.company/source/oauth/callback/facebook/` and then click **Save**.

9. Navigate to the **Use cases -> Customize** page.
10. Under **Permissions** click **Add** for the **email** permission.

Next, you need to obtain the App ID and the App Secret for the Facebook app, and enter those into your authentik source configuration.

11. Go back to the Dashboard, and in the bottom left in the navigation pane, click on **App settings -> Basic**.
12. Copy the **App ID** and the **App secret** values and temporarily store them in a safe place until you enter them into authentik.

Finally, you need to publish the Facebook app.

12. Go back to the Dashboard, and on the **Create and publish this app** page, follow the prompts.

## authentik configuration

1. Log into authentik as admin, and then navigate to **Directory -> Federation & Social login**
2. Click **Create**.
3. In the **New Source** box, for **Select type** select **Facebook OAuth Source** and then click **Next**.
4. Define the following fields:
    - **Name**: provide a descriptive name
    - **Slug**: leave default value (If you choose a different slug then the default, the URL will need to be updated to reflect the change)
    - **User matching mode**: leave default option unless other configuration is needed
    - **User path**: leave default option unless other configuration is needed
    - **Icon**: optionally you can select a specific icon of logo to display on the login form.
    - **Protocol settings**
        - **Consumer Key**: enter the **App ID** from Facebook
        - **Consumer Secret**: enter the **App Secret** from Facebook
        - **Scopes**: define any further access scopes
    - **Flow settings**
        - **Authentication flow**: leave the default `default-source-authentication` option.
        - **Enrollment flow**: leave the default `default-source-enrollment` option.
5. Click **Finish** to save your settings and close the box.

You now have Facebook as a source. Verify by checking that appears on the **Directory -> Federation & Social login** page in authentik.

:::note
For more details on how to display the new source on the authentik Login page refer to [Add Sources to default Login form](../../index.md#add-sources-to-default-login-page).
:::
