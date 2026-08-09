# Simplified Flow Executor

The Simplified Flow Executor is a limited fallback browser-side interpreter, written in TypeScript,
for authentik's Flow language, which controls transactions between the authentik server and its
interaction with users and the services to which those users are seeking to gain authentication and
authorization.

It exists primarily to support late versions of Microsoft Office365 and Microsoft Teams, older
software that still uses the MSEdge-18 and IE-11 _Trident_ web engine for web-based log-ins. It has
limited support for the full language, supporting only the following stages:

- identification
- password
- redirect
- autosubmit
- authenticator validation (both code and WebAuthn)

### License

This code is licensed under the [MIT License](https://www.tldrlegal.com/license/mit-license).
[A copy of the license](./LICENSE.txt) is included with this package.
