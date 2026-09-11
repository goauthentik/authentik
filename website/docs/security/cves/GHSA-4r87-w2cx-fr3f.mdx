# GHSA-4r87-w2cx-fr3f

_Reported by [@kamil-sawicki](https://github.com/kamil-sawicki), [@savio-doyensec](https://github.com/savio-doyensec), and [@szybnev](https://github.com/szybnev)_

## Broken access control in Shared Signals Framework stream management

### Summary

The Shared Signals Framework checked permissions only when a stream was created. The operations that read, change, disable, or delete an existing stream did not, so a low privileged user of an application integrated with a Shared Signals Framework provider could act on that application's event streams without holding the permission required to manage them.

### Patches

authentik 2026.5.5 and 2026.2.6 fix this issue.

### Impact

**This affects only Enterprise deployments that use the Shared Signals Framework, where a provider is linked to an application as its backchannel provider and that application also issues access tokens to its users. Deployments that do not use the Shared Signals Framework are not affected.**

Creating a stream required an explicit permission on the provider, but the operations acting on an existing stream performed no equivalent check. Any user who can sign in to that application could reach these operations and act on the application's streams without holding the stream management permission.

The exposed operations differ by version. On 2026.2, only stream deletion is reachable. On 2026.5, the read, update, verify, and status operations are reachable as well. In all cases this breaks the integrity and availability of the receiver's security event feed. It did not allow redirecting delivery to an attacker chosen destination or retrieving stored delivery credentials.

### Workarounds

None. Until you can upgrade, we recommend not relying on the Shared Signals Framework for delivery of security events, as a stream's configuration cannot be protected from tampering by users of the linked application on affected versions.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
