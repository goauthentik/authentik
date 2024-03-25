---
title: Applications
slug: /applications
---

Applications, as defined in authentik, are used to configure and separate the authorization/access control and the appearance of a specific software application in the **My applications** page.

When a user logs into authentik, they see a list of the applications for which authentik is configured to provide authentication and authorization (the applications that that they are authorized to use).

Applications are the "other half" of providers. They typically exist in a 1-to-1 relationship; each application needs a provider and every provider can be used with one application. Applications can, however, use specific, additional providers to augment the functionality of the main provider. For more information, see [Backchannel providers](./manage_apps.md#backchannel-providers).

Furthermore, the [RAC (Remote Access Control)](../providers/rac/index.md) feature uses a single application and a single provider, but multiple "endpoints". An endpoint defines each remote machine.

:::info
For information about creating and managing applications, refer to [Manage applications](./manage_apps.md).
:::

## Appearance

Applications are displayed to users when:

-   The user has access defined via policies (or the application has no policies bound)
-   A valid Launch URL is configured/could be guessed, this consists of URLs starting with http:// and https://

The following aspects can be configured:

-   _Name_: This is the name shown for the application card
-   _Launch URL_: The URL that is opened when a user clicks on the application. When left empty, authentik tries to guess it based on the provider

    You can use placeholders in the launch url to build them dynamically based on the logged in user. For example, you can set the Launch URL to `https://goauthentik.io/%(username)s`, which will be replaced with the currently logged in user's username.

    Only applications whose launch URL starts with `http://` or `https://` or are relative URLs are shown on the users' **My applications** page. This can also be used to hide applications that shouldn't be visible on the **My applications** page but are still accessible by users, by setting the _Launch URL_ to `blank://blank`.

-   _Icon (URL)_: Optionally configure an Icon for the application

    If the authentik server does not have a volume mounted under `/media`, you'll get a text input. This accepts absolute URLs. If you've mounted single files into the container, you can reference them using `https://authentik.company/media/my-file.png`.

    If there is a mount under `/media` or if [S3 storage](../installation/storage-s3.md) is configured, you'll instead see a field to upload a file.

-   _Publisher_: Text shown below the sapplication
-   _Description_: Subtext shown on the application card below the publisher
