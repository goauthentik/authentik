---
title: Applications
---

Applications, as defined in authentik, are used to configure and separate the authorization/access control and the appearance of a specific software application in the **My applications** page.

When a user logs into authentik, they see a list of the applications for which authentik is configured to provide authentication and authorization (the applications that they are authorized to use).

Applications are the "other half" of providers. They typically exist in a 1-to-1 relationship; each application needs a provider and every provider can be used with one application. Applications can, however, use specific, additional providers to augment the functionality of the main provider. For more information, see [Backchannel providers](./manage_apps.mdx#backchannel-providers).

Furthermore, the [RAC (Remote Access Control)](../providers/rac/index.md) feature uses a single application and a single provider, but multiple "endpoints". An endpoint defines each remote machine.

:::info
For information about creating and managing applications, refer to [Manage applications](./manage_apps.mdx).
:::

## Appearance

Applications are displayed to users when:

- The user has access defined via policies (or the application has no policies bound)
- A valid Launch URL is configured/could be guessed, this consists of URLs starting with http:// and https://

The following options can be configured:

- _Name_: This is the name shown for the application card
- _Launch URL_: The URL that is opened when a user clicks on the application. When left empty, authentik tries to guess it based on the provider

    You can use placeholders in the launch url to build them dynamically based on the logged in user. For example, you can set the Launch URL to `https://goauthentik.io/%(username)s`, which will be replaced with the currently logged in user's username.

    For a reference of all fields available, see [the API schema for the User object](https://api.goauthentik.io/reference/core-users-retrieve/).

    Only applications whose launch URL starts with `http://` or `https://` or are relative URLs are shown on the users' **My applications** page. This can also be used to hide applications that shouldn't be visible on the **My applications** page but are still accessible by users, by setting the _Launch URL_ to `blank://blank`.

- _Icon (URL)_: Optionally configure an Icon for the application. You can select from files uploaded to the [Files](../../customize/files.md) library or enter an absolute URL.

- _Publisher_: Text shown in the application card's expandable kebab menu (⋮)
- _Description_: Text shown in the application card's expandable kebab menu (⋮)
