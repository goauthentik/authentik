# GHSA-g9hc-mm35-wh9v

_Reported by [@hackking007](https://github.com/hackking007), [@akoul](https://github.com/akoul), [@sakilahamed](https://github.com/sakilahamed), [@Hama1cco](https://github.com/Hama1cco), [@g4nkd](https://github.com/g4nkd), [@Tan-JunWei](https://github.com/Tan-JunWei), [@calbebop](https://github.com/calbebop)_

## Recipient override in the SMS authenticator

### Summary

SMS authenticator setup could send its one-time code to a phone number chosen by whoever completes the setup, instead of the number the flow had already set or approved.

### Patches

authentik 2026.5.9 and 2026.8.7 fix this issue.

### Impact

**Only deployments where a flow sets or restricts the phone number before SMS authenticator setup are affected.**

If a user has not set up the SMS authenticator yet, an actor who knows their password can enroll a phone they control and sign in as that user.

### Workarounds

None. We recommend not setting up the SMS authenticator in flows that set or restrict the phone number until upgrading.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
