---
title: Get started with authentik Enterprise
<<<<<<< HEAD
description: "How to get started with authentik Enterprise"
=======
description: "Enable authentik Enterprise on a new or existing installation"
sidebar_position: 1
>>>>>>> c7841e311 (website/docs: Revamp Enterprise Docs. (#23920))
---

Installing authentik is exactly the same process for both the Enterprise version and our open source version. Enterprise features are enabled by installing a license.

## Before you begin

You need:

- A running, supported version of authentik.
- Administrator access to the authentik Admin interface.
- Access to an organization in the [Customer Portal](https://customers.goauthentik.io/).

For a new deployment, [install authentik](../install-config/index.mdx) before continuing.

## 1. Copy the Install ID

Each authentik installation has a unique Install ID that binds a license to that installation.

1. Log in to the authentik Admin interface.
2. Navigate to **Enterprise** > **Licenses**.
3. Copy the value under **Your Install ID**.

In a [multi-tenant deployment](../sys-mgmt/tenancy.md), each tenant has its own Install ID and requires its own license.

## 2. Obtain a license key

You can purchase a license from the **Your Install ID** card in the Admin interface or directly from the [Customer Portal](https://customers.goauthentik.io/).

When you purchase a license, provide the Install ID and the required internal and external user capacity. For the complete purchase workflow, see [Purchase a license](./manage-enterprise.md#purchase-a-license).

To request a trial or discuss an Enterprise Plus agreement, contact [hello@goauthentik.io](mailto:hello@goauthentik.io).

## 3. Install the license key

1. In the Admin interface, navigate to **Enterprise** > **Licenses**.
2. Click **Install**.
3. Paste the license key into **License key**.
4. Click **Install**.

The **Licenses** page displays the installed license, its internal and external user capacity, and its expiry date. The **Current license status** card displays the combined status and capacity of all active licenses for the installation.

If authentik rejects the key, verify that you copied the complete key and that its Install ID matches the current installation. Contact [Enterprise support](./enterprise-support.md) if a valid key still cannot be installed.

## Next steps

- Review the [Enterprise features](./enterprise-features.md) and configure the features that you need in the standard authentik documentation.
- Learn how authentik [counts licensed users](./manage-enterprise.md#about-users-and-licenses).
- Configure additional Customer Portal users to avoid relying on a single account for license access.
