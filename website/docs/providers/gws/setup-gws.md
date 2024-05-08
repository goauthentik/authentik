---
title: Configure Google Workspace
---

-   note about backchannel provider
-   create google cloud project
-   enable Admin SDK API
-   create credentials
-   Select Application data
-   Create key and download json
-   do the `Set up domain-wide delegation for a service account`
    -   Set the scopes to these
    -   `"https://www.googleapis.com/auth/admin.directory.user"`
    -   `"https://www.googleapis.com/auth/admin.directory.group"`
    -   `"https://www.googleapis.com/auth/admin.directory.group.member"`
-   need to get email of an admin user to delegate as?
    -   Not sure which permissions are required
