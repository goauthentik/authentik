---
title: File storage
---

Image files are used in authentik to add a logo to new applications that you add, or to a new source, and for defining the ["branded" look](../sys-mgmt/brands.md#branding-settings) of the authentik interface, with your company's logo and title, a favicon, or a background image for the flows.

authentik provides a central place for storing all such files, the `authentik/data/media/public` directory. By default, these files are stored in authentik's PostgreSQL database.

## Upload and manage files

To upload and use images files, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Files**.

    Here you can upload a new file, delete a file, and search for a file that you already uploaded.
