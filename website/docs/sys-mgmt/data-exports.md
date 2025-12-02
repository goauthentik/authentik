---
title: Data Exports
sidebar_label: Data Exports
authentik_enterprise: true
---

The enterprise version of authentik allows you to export data (currently, users and events) in CSV format for backup or analysis purposes.
For detailed instructions on exporting users and events, see [Export users](../users-sources/user/user_basic_operations.md#export-users) and [Export events](events/logging-events.md#export-events) respectively.

You can access past data exports from the **System Management** > **Data Exports** page.
This page displays a list of data exports created to date. Here you can view the query used for a specific export (by expanding the export row),
search exports by data type and user, download completed exports and delete exports you no longer need.

## Permissions

Note that creating or viewing a data export requires view permission on the data type being exported in addition to the respective permission or data exports.
