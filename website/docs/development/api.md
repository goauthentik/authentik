---
title: API
---

Starting with 2021.3.5, every authentik instance has a built-in API browser, which can be accessed at https://authentik.company/api/v2beta/.

To generate an API client, you can use the Swagger schema at https://authentik.company/api/v2beta/swagger.json.

While testing, the API requests are authenticated by your browser session. To send an API request from outside the browser, you need to set an `Authorization` header.

The value needs to be set to the base64-encoded token key.
