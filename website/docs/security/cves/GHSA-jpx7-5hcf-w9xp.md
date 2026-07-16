# GHSA-jpx7-5hcf-w9xp

_Reported by [@szybnev](https://github.com/szybnev), [@Su1ph3r](https://github.com/Su1ph3r), [@bl4cksku11](https://github.com/bl4cksku11), [@XlabAITeam](https://github.com/XlabAITeam), [@arthurscchan](https://github.com/arthurscchan), [@DavidKorczynski](https://github.com/DavidKorczynski), [@AdamKorcz](https://github.com/AdamKorcz)_

## Remote Access Control endpoints and their stored credentials are exposed to any authenticated user, and connections can cross application boundaries

### Summary

The Remote Access Control (RAC) endpoint list returned every configured endpoint to any authenticated user, regardless of which applications they were allowed to access, and the response included connection settings that can hold stored credentials. Separately, a user who could launch one RAC application could open a connection to an endpoint belonging to a different application they were never granted.

### Patches

authentik 2026.5.5 and 2026.2.6 fix this issue.

### Impact

**Affected: deployments using the enterprise Remote Access Control provider. Endpoint enumeration affects every such deployment; credential exposure affects any deployment that stores connection credentials for its endpoints. Deployments that do not use Remote Access Control are not affected.**

The endpoint listing did not apply the access controls that govern the endpoints themselves, and the connection flow did not confirm that the endpoint being opened belonged to the application it was launched through.

Any authenticated user could read every endpoint together with its host and any credentials stored on it, and could reach endpoints outside the applications granted to them.

This exposes the stored credentials for managed RDP, SSH, and VNC targets and grants interactive access to systems the user was never authorized to reach.

### Workarounds

None. We recommend not relying on Remote Access Control endpoint access rules until you upgrade, and rotating any connection credentials stored for RAC endpoints once you have.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
