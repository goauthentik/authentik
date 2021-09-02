---
title: API
---

Starting with 2021.3.5, every authentik instance has a built-in API browser, which can be accessed at https://authentik.company/api/v3/.

To generate an API client, you can use the OpenAPI v3 schema at https://authentik.company/api/v3/schema/.

While testing, the API requests are authenticated by your browser session.

To send an API request from outside the browser, you need to set the `Authorization` Header to `Bearer <your token>`.
