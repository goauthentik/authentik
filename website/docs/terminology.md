---
id: terminology
title: Terminology
---
### Policy

At a base level a policy is a yes/no gate. It will either evaluate to True or False depending on the Policy Kind and settings. For example, a "Group Membership Policy" evaluates to True if the user is member of the specified Group and False if not. This can be used to conditionally apply Stages, grant/deny access to various objects, and for other custom logic.

### Provider

A Provider is a way for other applications to authenticate against passbook. Common Providers are OpenID Connect (OIDC) and SAML.

### Source

Sources are locations from which users can be added to passbook. For example, an LDAP Connection to import Users from Active Directory, or an OAuth2 Connection to allow Social Logins.

### Application

An application links together Policies with a Provider, allowing you to control access. It also holds Information like UI Name, Icon and more.

### Stages

A stage represents a single verification or logic step. They are used to authenticate users, enroll users, and more. These stages can optionally be applied to a flow via policies.

### Flows

Flows are an ordered sequence of stages. These flows can be used to define how a user authenticates, enrolls, etc.

### Property Mappings

Property Mappings allow you to make information available for external applications. For example, if you want to login to AWS with passbook, you'd use Property Mappings to set the user's roles in AWS based on their group memberships in passbook.
