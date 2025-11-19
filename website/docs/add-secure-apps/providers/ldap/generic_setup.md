---
title: Create an LDAP provider
---

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

Creating an authentik LDAP provider requires the following steps:

1. Create an LDAP authentication flow _(optional)_
2. Create an LDAP application and provider
3. Create a service account and assign the LDAP search permission
4. Create an LDAP Outpost

## Create an LDAP authentication flow _(optional)_

The `default-authentication-flow` validates MFA by default. DUO, TOTP and static authenticators are supported by the LDAP provider (not WebAuthn or SMS).

If you plan to use only dedicated service accounts to bind to LDAP, or only use LDAP supported MFA authenticators, then you can use the default authentictation flow and skip this section and continue at [Create LDAP Application and Provider](#create-an-ldap-application-and-provider)

Refer to [Code-based MFA support](./index.md#code-based-mfa-support) for more information on LDAP and MFA.

### Create custom stages

You'll need to create the stages that make up the flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages**, and click **Create**.

#### Identification Stage

First, you'll need to create a Password Stage.

3. Select **Password Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-authentication-password-stage`).
    - For **Backends**, leave the default settings.
4. Click **Finish**

#### Password Stage

Next, you'll need to create an Identification Stage.

5. On the **Stages** page, click **Create**.
6. Select **Identification Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-identification-stage`).
    - For **User fields**, select `Username` and `Email` (and UPN if it is relevant to your setup).
    - Set **Password stage** to the Password Stage created in the previous section (e.g. `ldap-authentication-password-stage`)
7. Click **Finish**

#### User Login Stage

Finally, you'll need to create a User Login Stage.

8. On the **Stages** page, click **Create**.
9. Select **User Login Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-authentication-login-stage`).
10. Click **Finish**

### Create an LDAP authentication flow

Now you'll need to create the LDAP authentication flow and bind the previously created stages.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**, click **Create**, and set the following required configurations:
    - Provide a **Name**, **Title** and **Slug** for the flow (e.g. `ldap-authentication-flow`).
    - Set **Designation** to `Authentication`.
3. Click **Create**.
4. Click the name of the newly created flow, open the **Stage Bindings** tab, and click **Bind existing stage**.
5. Select the previously created LDAP Identification Stage (e.g.`ldap-identification-stage`), set the order to `10`, and click **Create**.
6. Click **Bind existing stage**.
7. Select the previously created LDAP User Login Stage (e.g.`ldap-authentication-login-stage`), set the order to `30`, and click **Create**.

## Create an LDAP application and provider

The LDAP application and provider can now be created.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create with Provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **LDAP Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure LDAP Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

:::info
If you followed the optional [Create an LDAP authentication flow](#create-an-ldap-authentication-flow-optional) section, ensure that you set **Bind flow** to newly created authentication flow (e.g. `ldap-authentication-flow`).
:::

## Create a service account

Create a service account to bind to LDAP with.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users** and click **New User**.
3. Provide a name for the service account (e.g. `ldapservice`) and click **Create**.
4. Click the name of the newly created service account.
5. Under **Recovery**, click **Set password**, provide a secure password for the account, and click **Update password**.

:::info Default DN of service account
The default DN of this user will be `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
:::

### Assign the LDAP search permission to the service account

The service account needs permissions to search the LDAP directory.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**
3. Click on the name of the newly created LDAP provider, then open the **Permissions** tab.
4. Click **Assign to new user**
5. For **User**, select a user to assign the full directory search permission to (e.g. `ldapservice`).
6. Enable the **Search full LDAP directory** permission and click **Assign**

## Create an LDAP Outpost

The LDAP provider requires the deployment of an LDAP [Outpost](../../outposts/index.mdx).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**, click **Create** and set the following required configurations:
    - Provide a **Name** for the outpost (e.g. `LDAP Outpost').
    - Set the **Type** as `LDAP`.
    - Set **Integration** to match your deployment method or manually deploy an outpost via [Docker-Compose](../../outposts/manual-deploy-docker-compose.md) or [Kubernetes](../../outposts/manual-deploy-kubernetes.md). For more information, refer to the [Outpost documentation](../../outposts/index.mdx).
    - Under **Applications**, select the LDAP application created in the previous section.
    - Under **Advanced settings**, set the required outpost configurations. For more information, refer to [Outpost Configuration](../../outposts/index.mdx#configuration)

3. Click **Create**.

:::warning Multiple LDAP providers
The LDAP Outpost selects different providers based on their Base DN. Adding multiple providers with the same Base DN will result in inconsistent access.
:::

## Configuration verification

You can test the LDAP provider by using the `ldapsearch` tool on Linux and macOS or the `dsquery` tool on Windows.

<Tabs
defaultValue="ldapsearch"
values={[
{ label: "ldapsearch", value: "ldapsearch" },
{ label: "dsquery", value: "dsquery" },
]}

> <TabItem value="ldapsearch">

To install the `ldapsearch` tool, use one of the following commands:

```shell
sudo apt-get install ldap-utils -y # Debian-based systems
sudo yum install openldap-clients -y # CentOS-based systems
brew install openldap #macOS based systems (requires Homebrew to be installed)
```

To search the LDAP directory using the previously created `ldapservice` service account, use the following command:

```shell
ldapsearch \
  -x \
  -H ldap://<LDAP outpost IP address>:389 \
  -D 'cn=ldapservice,ou=users,DC=ldap,DC=goauthentik,DC=io' \
  -w '<ldapuserpassword>' \
  -b 'DC=ldap,DC=goauthentik,DC=io' \
  '(objectClass=user)'
```

This example query will return all users and log the first successful attempt in an event in **Events** > **Logs**. By default, further successful logins from the same user are not logged as they are cached in the outpost, see [Bind modes](./index.md#bind-modes) for more information.

:::warning LDAPS
In production it is recommended to use LDAPS, which requires `ldaps://` as the protocol, and port number `636` rather than `389`. See [LDAPS](./index.md#ldaps-via-ssl-or-starttls) for more information.
:::

  </TabItem>
  <TabItem value="dsquery">

To search the LDAP directory using the previously created `ldapservice` service account, use the following command:

```powershell
dsquery * -s <LDAP outpost IP address> -u "cn=ldapservice,ou=users,DC=ldap,DC=goauthentik,DC=io" -p <ldapuserpassword> -b "DC=ldap,DC=goauthentik,DC=io" -filter "(objectClass=user)"
```

This example query will return all users and log the first successful attempt in an event in **Events** > **Logs**. By default, further successful logins from the same user are not logged as they are cached in the outpost, see [Bind modes](./index.md#bind-modes) for more information.

:::warning LDAPS
In production it is recommended to use LDAPS, which requires `ldaps://` as the protocol, and port number `636` rather than `389`. See [LDAPS](./index.md#ldaps-via-ssl-or-starttls) for more information.
:::

  </TabItem>
</Tabs>
