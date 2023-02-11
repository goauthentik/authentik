---
title: Troubleshooting CSRF Errors
---

With some proxy setups, you might run into CSRF errors when attempting to create/save objects in authentik. This is usually caused by either the _Origin_ or _Host_ header being incorrect.

Open the system info API endpoint of your authentik instance by going to *https://authentik.company/api/v3/admin/system/*. Take note of the value of _HTTP_HOST_, make sure it matches the domain you're accessing authentik at, and make sure it does _not_ include any port numbers.

When submitting a POST request by updating/creating an object, open the browser's developer tools and check the _Network_ tab. Open the POST request and look at the request headers. Make sure the value of _Origin_ matches your authentik domain, without any ports.
