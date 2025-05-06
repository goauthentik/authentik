---
title: Architecture overview
---

# authentik's architecture

authentik consists of several components that work together todo(dominic): finish sentence. This document provides an overview of these components and how they interact.

## Core components

authentik consists of a few larger components:

- **authentik server**: The actual application server, a Django project described in more detail below.
- **outpost-proxy**: A Go application based on a forked version of oauth2_proxy, which does identity-aware reverse proxying.
- **outpost-ldap**: A Go LDAP server that uses the authentik application server as its backend.
- **outpost-radius**: A Go RADIUS server that uses the authentik application server as its backend.
- **web**: The web frontend, both for administrating and using authentik. It is written in TypeScript using lit-html and the PatternFly CSS Library.
- **website**: The Website/documentation, which uses docusaurus.

## authentik server structure

authentik is at its very core a Django project. It consists of many individual django applications. These applications are intended to separate concerns, and they may share code between each other.

These are the current packages:

```
authentik
├── admin - Administrative tasks and APIs, no models (Version updates, Metrics, system tasks)
├── api - General API Configuration (Routes, Schema and general API utilities)
├── blueprints - Handle managed models and their state.
├── core - Core authentik functionality, central routes, core Models
├── crypto - Cryptography, currently used to generate and hold Certificates and Private Keys
├── enterprise - Enterprise features, which are source available but not open source
├── events - Event Log, middleware and signals to generate signals
├── flows - Flows, the FlowPlanner and the FlowExecutor, used for all flows for authentication, authorization, etc
├── lib - Generic library of functions, few dependencies on other packages.
├── outposts - Configure and deploy outposts on kubernetes and docker.
├── policies - General PolicyEngine
│   ├── dummy - A Dummy policy used for testing
│   ├── event_matcher - Match events based on different criteria
│   ├── expiry - Check when a user's password was last set
│   ├── expression - Execute any arbitrary python code
│   ├── password - Check a password against several rules
│   └── reputation - Check the user's/client's reputation
├── providers
│   ├── ldap - Provide LDAP access to authentik users/groups using an outpost
│   ├── oauth2 - OIDC-compliant OAuth2 provider
│   ├── proxy - Provides an identity-aware proxy using an outpost
│   ├── radius - Provides a RADIUS server that authenticates using flows
│   ├── saml - SAML2 Provider
│   └── scim - SCIM Provider
├── recovery - Generate keys to use in case you lock yourself out
├── root - Root django application, contains global settings and routes
├── sources
│   ├── ldap - Sync LDAP users from OpenLDAP or Active Directory into authentik
│   ├── oauth - OAuth1 and OAuth2 Source
│   ├── plex - Plex source
│   └── saml - SAML2 Source
├── stages
│   ├── authenticator_duo - Configure a DUO authenticator
│   ├── authenticator_static - Configure TOTP backup keys
│   ├── authenticator_totp - Configure a TOTP authenticator
│   ├── authenticator_validate - Validate any authenticator
│   ├── authenticator_webauthn - Configure a WebAuthn / Passkeys authenticator
│   ├── captcha - Make the user pass a captcha
│   ├── consent - Let the user decide if they want to consent to an action
│   ├── deny - Static deny, can be used with policies
│   ├── dummy - Dummy stage to test
│   ├── email - Send the user an email and block execution until they click the link
│   ├── identification - Identify a user with any combination of fields
│   ├── invitation - Invitation system to limit flows to certain users
│   ├── password - Password authentication
│   ├── prompt - Arbitrary prompts
│   ├── user_delete - Delete the currently pending user
│   ├── user_login - Login the currently pending user
│   ├── user_logout - Logout the currently pending user
│   └── user_write - Write any currently pending data to the user.
└── tenants - Soft tennancy, configure defaults and branding per domain
```

## Runtime architecture

The Django project is running in gunicorn, which spawns multiple workers and threads. Gunicorn is run from a lightweight Go application which reverse-proxies it, handles static files and will eventually gain more functionality as more code is migrated to go.

There are also several background tasks which run in Celery, the root celery application is defined in `authentik.root.celery`. 