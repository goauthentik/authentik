---
title: Duo authenticator setup stage
---

This stage configures a Duo authenticator. To get the API Credentials for this stage, open your Duo Admin dashboard.

Go to Applications, click on Protect an Application and search for "Auth API". Click on Protect.

Copy all of the integration key, secret key and API hostname, and paste them in the Stage form.

Devices created reference the stage they were created with, since the API credentials are needed to authenticate. This also means when the stage is deleted, all devices are removed.
