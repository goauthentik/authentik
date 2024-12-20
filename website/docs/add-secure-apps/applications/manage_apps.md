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

    - **Choose a Provider**: select the provider types for this application.

    - **Configure a Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and any additional required configurations.

    - **Configure Bindings**: to manage the listing and access to applications on a user's **My applications** page, you can optionally create a [binding](../flows-stages/bindings/index.md) between the application and a specific policy, group, or user. Note that if you do not define any bindings, then all users have access to the application. For more information about user access, refer to our documentation about [authorization](#policy-driven-authorization) and [hiding an application](#hide-applications).

4. On the **Review and Submit Application** panel, review the configuration for the new application and its provider, and then click **Submit**.

## Policy-driven authorization

To use a [policy](../../customize/policies/index.md) to control which users or groups can access an application, click on an application in the applications list and then select the **Policy/Group/User Bindings** tab. There you can bind users/groups/policies to grant them access. When nothing is bound, everyone has access. Binding a policy restricts access to specific Users or Groups, or by other custom policies such as restriction to a set time-of-day or a geographic region.

By default, all users can access applications when no policies are bound.

When multiple policies/groups/users are attached, you can configure the _Policy engine mode_ to either:

- Require users to pass all bindings/be member of all groups (ALL), or
- Require users to pass either binding/be member of either group (ANY)

## Application Entitlements

<span class="badge badge--preview">Preview</span>
<span class="badge badge--version">authentik 2024.12+</span>

Application entitlements can be used through authentik to manage authorization within an application (what areas of the app users or groups can access). Entitlements are scoped to a single application and can be bound to multiple users and/or groups (binding policies is not currently supported), giving them access to the entitlement. An application can either check for the name of the entitlement (via the `entitlements` scope), or via attributes stored in entitlements.

An authentik admin can create an entitlement [in the Admin interface](#create-an-application-entitlement) or using the [authentik API](../../developer-docs/api/api.md).

Because entitlements exist within an application, names of entitlements must be unique within an application. This also means that entitlements are deleted when an application is deleted.

### Using entitlements

Entitlements to which a user has access can be retrieved using the `user.app_entitlements()` function in property mappings/policies. This function needs to be passed the specific application for which to get the entitlements. For example:

```python
entitlements = [entitlement.name for entitlement in request.user.app_entitlements(provider.application)]
return {
    "entitlements": entitlements,
}
```

### Attributes

Each entitlement can store attributes similar to user and group attributes. These attributes can be accessed in property mappings and passed to applications via `user.app_entitlements_attributes`. For example:

```python
attrs = request.user.app_entitlements(provider.application)
return {
    "my_attr": attrs.get("my_attr")
}
```

### Create an application entitlement

1. Open the Admin interface and navigate to **Applications -> Applications**.
2. Click the name of the application for which you want to create an entitlement.
3. Click the **Application entitlements** tab at the top of the page, and then click **Create entitlement**. Provide a name for the entitlement, enter any optional **Attributes**, and then click **Create**.
4. In the list locate the entitlement to which you want to bind a user or group, and then **click the caret (>) to expand the entitlement details.**
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
