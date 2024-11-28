---
title: Manage applications
---

Managing the applications that your team uses involves several tasks, from initially adding the application and provider, to controlling access and visibility of the application, to providing access URLs.

## Add new applications

Learn how to add new applications from our video or follow the instructions below.

### Video

<iframe width="560" height="315" src="https://www.youtube.com/embed/broUAWrIWDI;start=22" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

### Instructions

To add an application to authentik and have it display on users' **My applications** page, you can use the Application Wizard, which creates both the new application and the required provider at the same time.

1. Log into authentik as an admin, and navigate to **Applications --> Applications**.

2. Click **Create with Wizard**. (Alternatively, use our legacy process and click **Create**. The legacy process requires that the application and its authentication provider be configured separately.)

3. In the **New application** wizard, define the application details, the provider type and configuration, and then click **Submit**.

4. To manage the display of the new application on the **My applications** page, you can optionally define the bindings for a specific policy, group, or user. Note that if you do not define bindings, then all users have access to the application, For more information, refer to [authorization](#authorization).

## Authorization

Application access can be configured using (Policy) bindings. Click on an application in the applications list, and select the _Policy / Group / User Bindings_ tab. There you can bind users/groups/policies to grant them access. When nothing is bound, everyone has access. You can use this to grant access to one or multiple users/groups, or dynamically give access using policies.

By default, all users can access applications when no policies are bound.

When multiple policies/groups/users are attached, you can configure the _Policy engine mode_ to either:

-   Require users to pass all bindings/be member of all groups (ALL), or
-   Require users to pass either binding/be member of either group (ANY)

## Hide applications

To hide an application without modifying its policy settings or removing it, you can simply set the _Launch URL_ to `blank://blank`, which will hide the application from users.

Keep in mind that users still have access, so they can still authorize access when the login process is started from the application.

## Launch URLs

To give users direct links to applications, you can now use a URL like `https://authentik.company/application/launch/<slug>/`. If the user is already logged in, they will be redirected to the application automatically. Otherwise, they'll be sent to the authentication flow and, if successful, forwarded to the application.

## Backchannel providers

Backchannel providers can augment the functionality of applications by using additional protocols. The main provider of an application provides the SSO protocol that is used for logging into the application. Then, additional backchannel providers can be used for protocols such as [SCIM](../providers/scim/index.md) and [LDAP](../providers/ldap/index.md) to provide directory syncing.

Access restrictions that are configured on an application apply to all of its backchannel providers.
