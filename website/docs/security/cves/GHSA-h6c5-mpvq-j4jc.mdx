# GHSA-h6c5-mpvq-j4jc

_Reported by [@tonghuaroot](https://github.com/tonghuaroot), [@Uhudsavasindankacanokcu2](https://github.com/Uhudsavasindankacanokcu2), [@oduoke567](https://github.com/oduoke567), [@szybnev](https://github.com/szybnev), [@Hann1bl3L3ct3r](https://github.com/Hann1bl3L3ct3r), [@voraci0us](https://github.com/voraci0us), [@everping](https://github.com/everping), [@4dollar4](https://github.com/4dollar4), [@arthurscchan](https://github.com/arthurscchan), [@DavidKorczynski](https://github.com/DavidKorczynski), [@AdamKorcz](https://github.com/AdamKorcz), [@r0hanSH](https://github.com/r0hanSH), [@thefoulowl](https://github.com/thefoulowl), [@bayramshirinov](https://github.com/bayramshirinov), [@MayankPandey01](https://github.com/MayankPandey01), [@DavidCarliez](https://github.com/DavidCarliez), [@XlabAITeam](https://github.com/XlabAITeam), [@keenanwgn](https://github.com/keenanwgn), [@pkuGenuine](https://github.com/pkuGenuine), [@liangjs](https://github.com/liangjs), [@A7um](https://github.com/A7um), [@KasperBuilds](https://github.com/KasperBuilds), [@cipher-creator](https://github.com/cipher-creator), [@antigone4224](https://github.com/antigone4224), [@JebeenLee](https://github.com/JebeenLee), [@senti-man](https://github.com/senti-man), [@Rorasaurus](https://github.com/Rorasaurus), [@Alpastx](https://github.com/Alpastx), [@code-and-covfefe](https://github.com/code-and-covfefe), [@riyandhiman14](https://github.com/riyandhiman14), [@0xDvc-RE](https://github.com/0xDvc-RE), [@rodrigoarrelaro](https://github.com/rodrigoarrelaro), [@owen050724](https://github.com/owen050724), [@cy3erm](https://github.com/cy3erm), [@Sn1r](https://github.com/Sn1r), [@chndlrx](https://github.com/chndlrx), [@moizxsec](https://github.com/moizxsec), [@anthonyk2923](https://github.com/anthonyk2923), [@isazajuancarlos](https://github.com/isazajuancarlos)_

## Privilege escalation via delegated group and user management

### Summary

An account with delegated permission to manage a single group, or a single user, could grant superuser status to any account, and could assign an existing role to a group, without holding the permissions that gate those privileges.

### Patches

authentik 2026.2.7, 2026.5.7 and 2026.8.2 fix this issue.

### Impact

**Only deployments that delegate group, group membership or user management to accounts which are not full administrators are affected.**

Groups form a hierarchy, and superuser status is inherited from any group above, so a group can confer it without holding it itself. The checks on group membership and on the hierarchy either did not look for superuser status, or looked only at the group's own setting. Nothing checked the permission to assign a role to a group.

### Workarounds

Restrict the permissions to create and modify groups, to modify users, and to add users to groups, so that all of them are held only by accounts that are already full administrators.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
