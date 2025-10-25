---
title: GitHub compatibility
---

The OAuth2 provider also exposes a GitHub-compatible endpoint. This endpoint can be used by applications, which support authenticating against GitHub Enterprise, but not generic OpenID Connect.

To use any of the GitHub Compatibility scopes, you have to use the GitHub Compatibility Endpoints.

| Endpoint        | URL                         |
| --------------- | --------------------------- |
| Authorization   | `/login/oauth/authorize`    |
| Token           | `/login/oauth/access_token` |
| User Info       | `/user`                     |
| User Teams Info | `/user/teams`               |

To access the user's email address, a scope of `user:email` is required. To access their groups, `read:org` is required. Because these scopes are handled by a different endpoint, they are not customisable as a Scope Mapping.

## Special scopes for GitHub compatibility

- `user`: No-op, is accepted for compatibility but does not give access to any resources
- `read:user`: Same as above
- `user:email`: Allows read-only access to `/user`, including email address
- `read:org`: Allows read-only access to `/user/teams`, listing all the user's groups as teams.
