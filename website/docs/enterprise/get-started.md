---
title: Get started
---

Installing authentik is exactly the same process for both Enterprise version and our free [open source](https://github.com/goauthentik/authentik) version.

## 1. Install Enterprise

To get started working with Enterprise authentik, [upgrade](../install-config/upgrade.mdx) to the [2023.8.x](../../releases/) version or later.

If this is a fresh install, refer to our [technical documentation](../install-config/index.mdx) for instructions to install and configure authentik.

- [Docker Compose installation](../install-config/install/docker-compose.mdx)
- [Kubernetes installation](../install-config/install/kubernetes.md)

## 2. Access Enterprise

Access your Enterprise features by first [purchasing a license](./manage-enterprise.mdx#buy-a-license) for the organization.

To open the Customer Portal and buy a license, go to the Admin interface and in the left pane, navigate to **Enterprise -> Licenses**, and then click **Go to Customer Portal**.

Alternatively you can open a new browser window and go directly to the [Customer Portal](https://customers.goauthentik.io/). If you do not yet have an authentik account, there is a [Sign up link](https://customers.goauthentik.io/signup) on the Customer Portal login page.

In the Customer Portal you [define your organization](./manage-enterprise.mdx#create-an-organization) and its members, manage your [licenses](./manage-enterprise.mdx#license-management) and [billing](./manage-enterprise.mdx#manage-billing), and access our [Support center](./entsupport.md).

:::info
A license is associated with a specific Organization in the customer portal and a specific authentik instance (with a unique Install ID), and not with individual users. A single license is purchased for a specified number of users. Additional users can be added to a license, or additional licenses purchased for the same instance, if more users need to be added later.
:::

## 3. Visit the Support center

Enterprise authentik provides dedicated support, with a Support center where you can open a request and view the progress and communications for your current requests.

:::info
Access to the Support Center and the ticketing system requires a licensed instance of authentik.
:::

To learn about our Support center, see ["Enterprise support"](./entsupport.md).
