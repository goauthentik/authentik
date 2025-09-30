---
title: Facebook
support_level: community
---

Allows users to authenticate using their Facebook credentials.

## Preparation

The following placeholders are used:

- `authentik.company` is the FQDN of the authentik installation.

## Facebook configuration

To integrate authentik with Facebook, you will need to register with Meta for Developers and create a developers account. Refer to the [Facebook documentation](https://developers.facebook.com/docs/development) for exact steps.

1. Visit https://developers.facebook.com/ and log in to your Facebook account.
2. After you log in, go to https://developers.facebook.com/async/registration and follow the steps to register as a developer.

Next, create an app so that Facebook generates a unique ID for your authentik app.

3. On the Meta for Developers Dashboard click **Create**.
4. Follow the prompts to create the app.

After you create the app you need to customize its login settings.

5. Go back to the Dashboard and in the left navigation pane click **Use Cases**.
6. On the **Use cases** page, click **Customize** under **Authentication and account creation**.
7. On the **Customize** page, click **Go to settings**.
8. On the **Facebook Login settings** page set the **Valid OAuth redirect URIs** field to `https://authentik.company/source/oauth/callback/facebook/` and then click **Save**.
9. Navigate to the **Use cases > Customize** page.
10. Under **Permissions** click **Add** for the **email** permission.

Next, you need to obtain the App ID and the App Secret for the Facebook app. These will be required when creating the source in authentik.

11. Go back to the Dashboard, and in the bottom left in the navigation pane, click **App settings > Basic**.
12. Take note of the **App ID** and the **App secret** values.

Finally, you need to publish the Facebook app.

12. Go back to the Dashboard, and on the **Create and publish this app** page, follow the prompts.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Facebook OAuth Source** as the source type.
    - **Create Facebook OAuth Source**: provide a name, a slug which must match the slug used in the Facebook `Valid OAuth redirect URIs` field, and the following required configurations:
        - **User matching mode**: leave default option unless other configuration is needed.
        - **User path**: leave default option unless other configuration is needed.
        - **Icon**: optionally you can select a specific icon or logo to display on the login form.
        - **Protocol settings**
            - **Consumer Key**: enter the **App ID** from Facebook.
            - **Consumer Secret**: enter the **App Secret** from Facebook.
            - **Scopes**: define any further access scopes.
        - **Flow settings**
            - **Authentication flow**: leave the default `default-source-authentication` option.
            - **Enrollment flow**: leave the default `default-source-enrollment` option.
3. Click **Finish** to save your settings and close the box.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::
