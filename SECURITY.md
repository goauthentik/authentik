authentik takes security very seriously. We follow the rules of [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure), and we urge our community to do so as well, instead of reporting vulnerabilities publicly. This allows us to patch the issue quickly, announce it's existence and release the fixed version.

## Independent audits and pentests

In May/June of 2023 [Cure53](https://cure53.de) conducted an audit and pentest. The [results](https://cure53.de/pentest-report_authentik.pdf) are published on the [Cure53 website](https://cure53.de/#publications-2023). For more details about authentik's response to the findings of the audit refer to [2023-06 Cure53 Code audit](https://goauthentik.io/docs/security/2023-06-cure53).

## What authentik classifies as a CVE

CVE (Common Vulnerability and Exposure) is a system designed to aggregate all vulnerabilities. As such, a CVE will be issued when there is a either vulnerability or exposure. Per NIST, A vulnerability is:

“Weakness in an information system, system security procedures, internal controls, or implementation that could be exploited or triggered by a threat source.”

If it is determined that the issue does qualify as a CVE, a CVE number will be issued to the reporter from GitHub.

Even if the issue is not a CVE, we still greatly appreciate your help in hardening authentik.

## Supported Versions

(.x being the latest patch release for each version)

| Version  | Supported |
| -------- | --------- |
| 2024.4.x | ✅        |
| 2024.6.x | ✅        |

## Reporting a Vulnerability

To report a vulnerability, send an email to [security@goauthentik.io](mailto:security@goauthentik.io). Be sure to include relevant information like which version you've found the issue in, instructions on how to reproduce the issue, and anything else that might make it easier for us to find the issue.

## Severity levels

authentik reserves the right to reclassify CVSS as necessary. To determine severity, we will use the CVSS calculator from NVD (https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator). The calculated CVSS score will then be translated into one of the following categories:

| Score      | Severity |
| ---------- | -------- |
| 0.0        | None     |
| 0.1 – 3.9  | Low      |
| 4.0 – 6.9  | Medium   |
| 7.0 – 8.9  | High     |
| 9.0 – 10.0 | Critical |

## Disclosure process

1. Report from Github or Issue is reported via Email as listed above.
2. The authentik Security team will try to reproduce the issue and ask for more information if required.
3. A severity level is assigned.
4. A fix is created, and if possible tested by the issue reporter.
5. The fix is backported to other supported versions, and if possible a workaround for other versions is created.
6. An announcement is sent out with a fixed release date and severity level of the issue. The announcement will be sent at least 24 hours before the release of the security fix.
7. The fixed version is released for the supported versions.

## Getting security notifications

To get security notifications, subscribe to the mailing list [here](https://groups.google.com/g/authentik-security-announcements) or join the [discord](https://goauthentik.io/discord) server.
