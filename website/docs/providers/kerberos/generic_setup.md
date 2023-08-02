---
title: Generic Setup
---

### Kerberos Flow

This part is optional if using the provided `default-authentication-identification` flow.

#### Create Custom Stages

1. Create a new identification stage. _Flows & Stage_ -> _Stages_ -> _Create_
   ![](./generic_setup_flow_stage_identification_create.png)
2. Name it something meaningful like `kerberos-identification-stage`. Select User fields Username.
   ![](./generic_setup_flow_stage_identification_config.png)
3. Create a new password stage. _Flows & Stage_ -> _Stages_ -> _Create_
   ![](./generic_setup_flow_stage_password_create.png)
4. Name it something meaningful like `kerberos-authentication-password`. Leave the defaults for Backends.
   ![](./generic_setup_flow_stage_password_config.png)
5. Create a new user login stage. _Flows & Stage_ -> _Stages_ -> _Create_
   ![](./generic_setup_flow_stage_user_login_create.png)
6. Name it something meaningful like `kerberos-authentication-login`. Session settings are ignored.
   ![](./generic_setup_flow_stage_user_login_config.png)

#### Create Custom Flow

1. Create a new authentication flow under _Flows & Stage_ -> _Flows_ -> _Create_, and name it something meaningful like `kerberos-authentication-flow`
   ![](./generic_setup_flow_create.png)
2. Click the newly created flow and choose _Stage Bindings_.
   ![](./generic_setup_flow_stage_bindings.png)
3. Click `Bind exising stage` choose `kerberos-identification-stage` and set the order to `10`.
   ![](./generic_setup_flow_stage_bindings_identification.png)
4. Click `Bind existing stage` choose `kerberos-authentication-login` and set the order to `30`.
   ![](./generic_setup_flow_stage_bindings_authentication.png)
5. Edit the `kerberos-identification-stage`.
   ![](./generic_setup_flow_stage_bindings_identification_edit.png)
6. Change the Password stage to `kerberos-authentication-password`.
   ![](./generic_setup_flow_stage_bindings_password.png)

### Create Kerberos Realm

1. Create the Kerberos Realm under _Directory_ -> _Kerberos Realms_. Enter the realm name and choose the previously created authentication flow, or the `default-authentication-identification`, depending on the setup.
   ![](./generic_setup_realm_create.png)

### Create Kerberos Provider

1. Create the Kerberos Provider under _Applications_ -> _Providers_ -> _Create_.
   ![](./generic_setup_provider_create.png)
2. Name is something meaningful like `Samba` (example for a Samba share), the service principal name, and select the previously created realm.
   ![](./generic_setup_provider_config.png)

### Create Kerberos Application

1. Create the Kerberos Application under _Applications_ -> _Applications_ -> _Create_ and name it something meaningful like `LDAP`. Choose the provider created in the previous step.
   ![](./generic_setup_application_create.png)

### Create Kerberos Outpost

This step is optional if you don't need an outpost.

1. Create the Kerberos Outpost under _Applications_ -> _Outposts_ -> _Create_. Set the Type to `Kerberos` and choose the previously created realm.
   ![](./generic_setup_outpost_create.png)

:::info
Only one realm can be selected by outpost. If you have multiple realms, one outpost must be created per-realm. However, multiple outpost can be created for the same realm.
:::

### MIT Krb5 Test

Test connectivity by using MIT krb5.

:::info
krb5 can be installed on Linux system with these commands

```shell
sudo apt-get install krb5-user -y # Debian-based systems
sudo yum install krb5-workstation krb5-libs krb5-auth-dialog -y # CentOS-based systems
```

:::

First download the `krb5.conf` from the realm page and store it under `/etc/krb5.conf`. If you do not have permissions for `/etc/krb5.conf`, store it anywhere you can, like `~/krb5.conf` and run `export KRB5_CONFIG=~/krb5.conf`.

If you deployed an outpost, you can edit the `krb5.conf` file and change the line `kdc = https://...` with `kdc = <Kerberos Outpost IP address>:8888`. You can also add the DNS records provided on the realm page for automatic KDC discovery.

```shell
kinit <your username>@<your realm>
klist
kvno cifs/server.authentik.company@<your realm>
klist
```

:::info
This query will log the first successful attempt in an event in the Events -> Logs area.

The `klist` command will show the obtained tickets.
:::

For further debugging, consider running `export KRB5_TRACE=/dev/stderr` to get verbose logs from krb5.
