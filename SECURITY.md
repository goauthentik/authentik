authentik takes security very seriously. We follow the rules of [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure), and we urge our community to do so as well, instead of reporting vulnerabilities publicly. This allows us to patch the issue quickly, announce it's existence and release the fixed version.

## Independent audits and pentests

We are committed to engaging in regular pentesting and security audits of authentik. Defining and adhering to a cadence of external testing ensures a stronger probability that our code base, our features, and our architecture is as secure and non-exploitable as possible. For more details about specific audits and pentests, refer to "Audits and Certificates" in our [Security documentation](https://docs.goauthentik.io/docs/security).

## What authentik classifies as a CVE

CVE (Common Vulnerability and Exposure) is a system designed to aggregate all vulnerabilities. As such, a CVE will be issued when there is a either vulnerability or exposure. Per NIST, A vulnerability is:

“Weakness in an information system, system security procedures, internal controls, or implementation that could be exploited or triggered by a threat source.”

If it is determined that the issue does qualify as a CVE, a CVE number will be issued to the reporter from GitHub.

Even if the issue is not a CVE, we still greatly appreciate your help in hardening authentik.

## Supported Versions

(.x being the latest patch release for each version)

| Version    | Supported  |
| ---------- | ---------- |
| 2025.8.x   | ✅         |
| 2025.10.x  | ✅         |

## Reporting a Vulnerability

If you discover a potential vulnerability, please report it responsibly through one of the following channels:

- **Email**: [security@goauthentik.io](mailto:security@goauthentik.io)
- **GitHub**: Submit a private security advisory via our [repository’s advisory portal](https://github.com/goauthentik/authentik/security/advisories/new)

When submitting a report, please include as much detail as possible, such as:

- **Affected version(s)**: The version of authentik where the issue was identified.
- **Steps to reproduce**: A clear description or proof of concept to help us verify the issue.
- **Impact assessment**: How the vulnerability could be exploited and its potential effect.
- **Additional information**: Logs, configuration details (if relevant), or any suggested mitigations.

We kindly ask that you do not disclose the vulnerability publicly until we have confirmed and addressed the issue.

Our team will:

- Acknowledge receipt of your report as quickly as possible.
- Keep you updated on the investigation and resolution progress.

## Researcher Recognition

We value contributions from the security community. For each valid report, we will publish a dedicated entry on our Security Advisory page that optionally includes the reporter’s name (or preferred alias). Please note that while we do not currently offer monetary bounties, we are committed to giving researchers appropriate credit for their efforts in keeping authentik secure.

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
