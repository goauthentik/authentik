---
title: Telegram
support_level: community
---

Configuring Telegram as a source allows users to authenticate using their Telegram account credentials within authentik.

## Telegram

To use Telegram as a source, you first need to register a Telegram bot:

1. Start a chat with `@BotFather` on Telegram.
2. Use `/newbot` command to create a new bot. Pick a username for your new bot (e.g., `my_bot`).
   Note the username you've chosen - you'll need it when setting up the source in authentik.
3. BotFather will provide you with a token for your bot. Make a record of the token as well.
4. Link the bot to your authentik domain name using `/setdomain` command.
   Please note that **the domain name must exactly match the FQDN of the authentik installation**.

Now that the bot is configured you can proceed to creating a source in authentik.

## authentik

In authentik, open the Admin interface and go to **Directory** > **Federation & Social login** and click **Create**.
Select **Telegram source** and configure your source:

- **Name**: Define a name.
- **Slug**: Set a slug.
- **Bot username**: Set the username of your Telegram bot (e.g., `my_bot`).
- **Bot token**: Set the token of your Telegram bot.
- **Request access to send messages from your bot**: enable this if you need your bot to be able to
  send messages to the users who logged in to authentik with it.

Save, and you now have Telegram as a source.

:::note
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

## Telegram source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

### Expression data

The following variables are available to OAuth source property mappings:

- `info`: A Python dictionary containing Telegram user data:
    - `id` - Telegram user ID
    - `username` - Username of the user. Might not be present.
    - `first_name` - First name of the user. Might not be present.
    - `last_name` - Last name of the user. Might not be present.
    - `photo_url` - URL of the user's profile photo. May not be present
