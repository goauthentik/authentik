---
title: Telegram
support_level: community
---

Configuring Telegram as a source allows users to authenticate within authentik using their Telegram account credentials.

## Preparation

Using Telegram as a source requires that your authentik instance is served from a domain.

## Telegram configuration

To use Telegram as a source, you first need to register a Telegram bot:

1. Start a chat with `@BotFather` on Telegram.
2. Use the `/newbot` command to create a new bot. Define a name and username for your new bot (e.g., `authentik_bot`).
3. BotFather will provide you with a token for the new bot. Take note of the username and token because they will be required when setting up the source in authentik.
4. Link the bot to your authentik domain name using the `/setdomain` command.

:::note
The domain name set in Telegram must **exactly** match the FQDN of the authentik installation.
:::

Now that the bot is configured you can proceed to creating a source in authentik.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Telegram** as the source type.
    - **Create Telegram Source**: provide a name, a slug, and the following required configurations:
        - **Bot username**: The username of your Telegram bot (e.g., `authentik_bot`).
        - **Bot token**: The token of your Telegram bot.
        - **Request access to send messages from your bot**: enable this to allow your bot to send messages to authentik users utilizing the Telegram source for authentication.

3. Click **Save**.

:::note
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

## Telegram source property mappings

[Property mappings](../../property-mappings/index.md) can be used to map Telegram user properties to authentik user properties.

### Expression data

Telegram user data is accessible to Telegram source property mappings as a dictionary named `info`.
The dictionary contains the following fields:

- `id` - Telegram user ID
- `username` - Username of the user. Might not be present.
- `first_name` - First name of the user. Might not be present.
- `last_name` - Last name of the user. Might not be present.
- `photo_url` - URL of the user's profile photo. Might not be present.

## Resources

- [Telegram Documentation - BotFather](https://core.telegram.org/bots/features#botfather)
