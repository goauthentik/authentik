---
title: Files
---

Image files are used in authentik to add an icon to new applications that you add, or to a new source, and for defining the ["branded" look](../sys-mgmt/brands/index.md#branding-settings) of the authentik interface, with your company's logo and title, a favicon, or a background image for the flows.

authentik provides a centralized file management system for storing and organizing these files. Files can be uploaded and managed from **Customization** > **Files** in the Admin interface. By default, files are stored on disk in the `/data` directory, but [S3 storage](../sys-mgmt/ops/storage-s3.md) can also be configured.

## Upload and manage files

To upload and use image files, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Files**.

    Here you can upload a new file, delete a file, and search for a file that you already uploaded.

:::info Using image URLs
Instead of uploading an image file to be used as an application's icon or source's icon, you can instead modify the specific object (application or source) and enter the URL for the image you want to use for that object.
:::
