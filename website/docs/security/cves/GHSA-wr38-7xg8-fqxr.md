# GHSA-5wcc-hf24-rf5h

## `UserSourceConnection.user` and `GroupSourceConnection.group` are changeable through the API

### Summary

An attacker with the ability to change a source connection, and an account in one of the configured sources can log into any account.

### Patches

authentik 2026.5.1, 2026.2.4, and 2025.12.6 fix this issue.

### Impact

`UserSourceConnection.user` and `GroupSourceConnection.group` are changeable through the API. This lets attackers with low privilege (`*_usersourceconnection`, `*_group*sourceconnection`) misrepresent users/groups as if they were coming from a specific source, with a specific identifier, then authenticate as the victim through that source and identifier.

### Workarounds

Ensure that `*_usersourceconnection`, `*_group*sourceconnection` permissions are only given to trusted admins.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
