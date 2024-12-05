# GHSA-rjvp-29xq-f62w

_Reported by [@devSparkle](https://github.com/devSparkle)_

## Potential Installation takeover when default admin user is deleted

### Summary

In the affected versions, when the default admin user has been deleted, it is potentially possible for an attacker to set the password of the default admin user without any authentication.

### Patches

authentik 2023.8.4 and 2023.10.2 fix this issue, for other versions the workaround can be used.

### Impact

authentik uses a blueprint to create the default admin user, which can also optionally set the default admin users' password from an environment variable. When the user is deleted, the `initial-setup` flow used to configure authentik after the first installation becomes available again.

### Workarounds

Ensure the default admin user (Username `akadmin`) exists and has a password set. It is recommended to use a very strong password for this user, and store it in a secure location like a password manager. It is also possible to deactivate the user to prevent any logins as akadmin.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
