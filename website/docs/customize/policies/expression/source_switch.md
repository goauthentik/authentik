---
title: Switch which source is used based on email address
---

You can use an expression policy to determine with source (a set of user credentials and data, stored in authentik, Google, GitHub, etc) is used for a particular user, based on which email address the user enters when they log in and authenticate (using the authn flow).

To define which source is used, [create an expression policy](../working_with_policies.md#create-a-policy) that defines the possible oiptions for the source, and the logic to determine the domain based on the email address and then "switch" the user to the desired source.
