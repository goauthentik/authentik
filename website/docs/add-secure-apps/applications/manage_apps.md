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

3. In the **New application** wizard, define the application details, the provider type, bindings for the application.

- **Application**: provide a name, an optional group for the type of application, the policy engine mode, and optional UI settings.

- **Choose a Provider**: Select the provider types for this application.

- **Configure a Provider**: Provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and any additional required configurations.

- **Configure Bindings**: To manage the display of the new application on the **My applications** page, you can optionally define [bindings](../flows-stages/bindings/index.md) for a specific policy, group, or user. To do so in the Wizard, click **Bind existing policy/group/user** to add a binding. You can select an existing policy binding, or create a new binding specifically for a group or user. For example, if you select **User** and then choose an existing user from the drop-down menu, you create a new binding between the user and this specific application. Note that if you do not define any bindings, then all users have access to the application. For more information, refer to [authorization](#authorization).

4. On the **Review and Submit Application** panel, review the configuration for the new application and its provider, and then click **Submit**.

## Authorization

Application access can be configured using either (Policy) bindings or Application Entitlements.

### Policy-driven authorization

To use a policy to control which users or groups can access an application, click on an application in the applications list, and select the **Policy/Group/User Bindings** tab. There you can bind users/groups/policies to grant them access. When nothing is bound, everyone has access. Binding a policy restricts access to specific Users or Groups, or by other custom policies such as restriction to a set time-of-day or a geographic region.

By default, all users can access applications when no policies are bound.

When multiple policies/groups/users are attached, you can configure the _Policy engine mode_ to either:

- Require users to pass all bindings/be member of all groups (ALL), or
- Require users to pass either binding/be member of either group (ANY)

### Application Entitlements

Another method to control which users or groups can access an application is to create an Application Entitlement (which defines the specific application(s)), and then bind that to specific groups or users.

1. To create an Application Entitlement open the Admin interface and navigate to **Applications -> Applications**.
2. Click the name of the application to which you want to add an entitlement.
3. Click the **Application entitlements** tab at the top of the page, and then click **Create entitlement**. Provide a name for the entitlement, enter any optional **Attributes**, and then click **Create**.
4. Locate the entitlement to which you want to bind a user or group, and then **click the caret (>) to expand the entitlement details.**
5. In the expanded area, click **Bind existing Group/User**.
6. In the **Create Binding** modal box, select either the tab for **Group** or **User**, and then in the drop-down list, select the group or user.
7. Optionally, configure additional settings for the binding, and then click **Create** to create the binding and close the modal box.

## Hide applications

To hide an application without modifying its policy settings or removing it, you can simply set the _Launch URL_ to `blank://blank`, which will hide the application from users.

Keep in mind that users still have access, so they can still authorize access when the login process is started from the application.

## Launch URLs

To give users direct links to applications, you can now use a URL like `https://authentik.company/application/launch/<slug>/`. If the user is already logged in, they will be redirected to the application automatically. Otherwise, they'll be sent to the authentication flow and, if successful, forwarded to the application.

## Backchannel providers

Backchannel providers can augment the functionality of applications by using additional protocols. The main provider of an application provides the SSO protocol that is used for logging into the application. Then, additional backchannel providers can be used for protocols such as [SCIM](../providers/scim/index.md) and [LDAP](../providers/ldap/index.md) to provide directory syncing.

Access restrictions that are configured on an application apply to all of its backchannel providers.
