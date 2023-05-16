Authentik takes security very seriously. We follow the rules of [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure), and we urge our community to do so as well, instead of reporting vulnerabilities publicly. This allows us to patch the issue quickly, announce it's existence and release the fixed version.

## Supported Versions

(.x being the latest patch release for each version)

| Version   | Supported          |
| --------- | ------------------ |
| 2023.4.x  | :white_check_mark: |
| 2023.5.x  | :white_check_mark: |

## Reporting a Vulnerability

To report a vulnerability, send an email to [security@goauthentik.io](mailto:security@goauthentik.io). Be sure to include relevant information like which version you've found the issue in, instructions on how to reproduce the issue, and anything else that might make it easier for us to find the bug.

## Criticality levels

### High

-   Authorization bypass
-   Circumvention of policies

### Moderate

-   Denial-of-Service attacks

### Low

-   Unvalidated redirects
-   Issues requiring uncommon setups

## Disclosure process

1. Issue is reported via Email as listed above.
2. The authentik Security team will try to reproduce the issue and ask for more information if required.
3. A criticality level is assigned.
4. A fix is created, and if possible tested by the issue reporter.
5. The fix is backported to other supported versions, and if possible a workaround for other versions is created.
6. An announcement is sent out with a fixed release date and criticality level of the issue. The announcement will be sent at least 24 hours before the release of the fix
7. The fixed version is released for the supported versions.

## Getting security notifications

To get security notifications, subscribe to the mailing list [here](https://groups.google.com/g/authentik-security-announcements) or join the [discord](https://goauthentik.io/discord) server.
