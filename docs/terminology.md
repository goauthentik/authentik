### Policy

A Policy is at a base level a yes/no gate. It will either evaluate to True or False depending on the Policy Kind and settings. For example, a "Group Membership Policy" evaluates to True if the User is member of the specified Group and False if not. This can be used to conditionally apply Stages, grant/deny access to various objects and is also used for other custom logic.

### Provider

A Provider is a way for other Applications to authenticate against passbook. Common Providers are OpenID Connect (OIDC) and SAML.

### Source

Sources are ways to get users into passbook. This might be an LDAP Connection to import Users from Active Directory, or an OAuth2 Connection to allow Social Logins.

### Application

An application links together Policies with a Provider, allowing you to control access. It also holds Information like UI Name, Icon and more.

### Flows

Flows are a method of describing a sequence of stages. These flows can be used to defined how a user authenticates, enrolls, etc.

### Stages

A stage represents a single verification or logic step. They are used to authenticate users, enroll them, and more. These stages can optionally be applied to a flow via policies.

### Property Mappings

Property Mappings allow you to make Information available for external Applications. For example, if you want to login to AWS with passbook, you'd use Property Mappings to set the User's Roles based on their Groups.
