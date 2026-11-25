# GHSA-pvq8-8pj6-m4r4

_Reported by [@researchatfluidattacks](https://github.com/researchatfluidattacks)_

## Cross-site scripting via notification links

### Summary

Clicking a link in a notification ran any script the link contained.

### Patches

authentik 2026.5.9 and 2026.8.7 fix this issue.

### Impact

**Deployments where notification rules deliver local notifications to users are affected. By default, only superusers and outposts can exploit this issue.**

Anyone allowed to create events can trigger such a notification and run JavaScript in the session of whoever clicks its link.

### Workarounds

None. We recommend not clicking links in notifications until upgrading.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
