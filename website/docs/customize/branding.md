---
title: Branding
slug: /branding
---

You can configure several branding options depending on the associated domain, even though objects such as applications, providers, etc. are still global. This can be handy if you want to use the same authentik instance, but brand it differently for different domains.

The main settings that control your instance's appearance and behavior are the **Branding settings** on your brand, and the default flows that you specify.

## Branding settings

The [_branding settings_](../sys-mgmt/brands/index.md#branding-settings) control the title, logo, and favicon that are displayed in your authentik instance. Here you can also select a specific image as your default flow background image, meaning it will display as the background for all flows. Note that you can override this image on a per-flow basis. You can also add [custom CSS](../sys-mgmt/brands/custom-css.mdx) to further customize the look of your instance.

Review our tips for using images and icons in the [Image optimization](../sys-mgmt/brands/index.md#image-optimization) section.

## Default flows

As another way to customize your authentik instance, you can specify the [_default flows_](../sys-mgmt/brands/index.md#default-flows) that you want authentik to use.

To create or modify a brand, open the Admin interface and navigate to **System** > **Brands**. For complete instructions refer to our [Brands documentation](../sys-mgmt/brands/index.md).
