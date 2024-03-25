---
title: Source stage
---

<span class="badge badge--primary">Enterprise</span>
<span class="badge badge--info">authentik 2024.4+</span>

---

The source stage injects an [OAuth](../../../../integrations/sources/oauth/) or [SAML](../../../../integrations/sources/saml/) Source into the flow execution. This allows for additional user verification, or to dynamically access different sources for different user identifiers (username, email address, etc).

```mermaid
sequenceDiagram
    participant u as User
    participant ak as authentik
    participant eidp as External IDP

    u->>ak: User initiates flow
    ak->>u: User reaches Source Stage

    u->>eidp: User is redirected to external IDP
    eidp->>ak: User has authenticated with external IDP

    alt User is connected to external IDP (auth)
        ak->>u: Source's authentication flow is started
        u->>ak: User finishes source's authentication flow
    else User has not been connected to external IDP (enroll)
        ak->>u: Source's enrollment flow is started
        u->>ak: User finishes source's enrollment flow
    end

    ak->>u: Execution of the previous flow is resumed
```

### Considerations

It is very important that the configured source's authentication and enrollment flows (when set; they can be left unselected to prevent authentication or enrollment with the source) do **not** have a [User login stage](../user_login/index.md) bound to them.

This is because the Source stage works by appending a [dynamic in-memory](../../../core/terminology.md#dynamic-in-memory-stage) stage to the source's flow, so having a [User login stage](../user_login/index.md) bound will cause the source's flow to not resume the original flow it was started from, and instead directly authenticating the pending user.

### Options

#### `source`

The source the user is redirected to. Must be a web-based source, such as [OAuth](../../../../integrations/sources/oauth/) or [SAML](../../../../integrations/sources/saml/). Sources like [LDAP](../../../../integrations/sources/ldap/) are _not_ compatible.

#### `resume_timeout`

Because the execution of the current flow is suspended before the user is redirected to the configured source, this option configures how long the suspended flow is saved. If this timeout is exceeded, upon return from the configured source, the suspended flow will restart from the beginning.
