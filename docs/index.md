# Welcome

Welcome to the passbook Documentation. passbook is an open-source Identity Provider and Usermanagement software. It can be used as a central directory for users or customers and it can integrate with your existing Directory.

passbook can also be used as part of an Application to facilitate User Enrollment, Password recovery and Social Login.

passbook uses the following Terminology:

### Policy

A Policy is at a base level a yes/no gate. It will either evaluate to True or False depending on the Policy Kind and settings. For example, a "Group Membership Policy" evaluates to True if the User is member of the specified Group and False if not. This can be used to conditionally apply Factors and grant/deny access.

### Provider

A Provider is a way for other Applications to authenticate against passbook. Common Providers are OpenID Connect (OIDC) and SAML.

### Source

Sources are ways to get users into passbook. This might be an LDAP Connection to import Users from Active Directory, or an OAuth2 Connection to allow Social Logins.

### Application

An application links together Policies with a Provider, allowing you to control access. It also holds Information like UI Name, Icon and more.

### Factors

Factors represent Authentication Factors, like a Password or OTP. These Factors can be dynamically enabled using policies. This allows you to, for example, force users from a certain IP ranges to complete a Captcha to authenticate.

### Property Mappings

Property Mappings allow you to make Information available for external Applications. For example, if you want to login to AWS with passbook, you'd use Property Mappings to set the User's Roles based on their Groups.
