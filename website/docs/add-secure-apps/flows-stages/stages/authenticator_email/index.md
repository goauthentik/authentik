---
title: Email authenticator setup stage
authentik_version: "2025.2"
---

The Email Authenticator Setup stage registers an email-based authenticator for the current user, enabling one-time codes to be sent via email during subsequent authentications.

## Overview

During enrollment, the user supplies an email address if one is not already known, then confirms ownership by entering a one-time code.

The enrolled email address can later be used with the [Authenticator Validation stage](../authenticator_validate/index.md).

## Configuration options

- **Use global connection settings**: use authentik's global email configuration instead of stage-specific SMTP settings.
- **SMTP host**: SMTP server hostname for stage-specific email delivery.
- **SMTP port**: SMTP server port.
- **SMTP username**: optional SMTP username.
- **SMTP password**: optional SMTP password.
- **Use TLS**: enable STARTTLS for the SMTP connection.
- **Use SSL**: enable SMTPS for the SMTP connection.
- **Timeout**: SMTP connection timeout in seconds.
- **From address**: sender address used for enrollment emails.
- **Token expiry**: how long the one-time code stays valid.
- **Subject**: subject line for the enrollment email.
- **Template**: email template used for the one-time code email.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that lets users enroll this authenticator from user settings.

For SMTP requirements and global email delivery settings, see [Email configuration](../../../../install-config/email.mdx).

## Flow integration

Use this stage in an enrollment or user-settings flow where the user should add an email authenticator.

To use the enrolled address during login, add an [Authenticator Validation stage](../authenticator_validate/index.md) to the authentication flow and allow the **Email** device class.

## Notes

- If **Use global connection settings** is enabled, configure the global email settings first. See the installation docs for [Docker Compose](../../../../install-config/install/docker-compose#email-configuration-optional-but-recommended) and [Kubernetes](../../../../install-config/install/kubernetes#email-configuration-optional-but-recommended).
- This stage is separate from the general-purpose [Email stage](../email/index.md), which is used for email verification and recovery.
- If the user already has an email address on their account, authentik can use that address during enrollment instead of prompting for a new address.
