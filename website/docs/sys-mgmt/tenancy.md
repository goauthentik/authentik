---
title: Tenancy
authentik_enterprise: true
---

::::warning
This feature is in alpha. Use at your own risk.
::::

::::info
This feature is available from 2024.2 and is not to be confused with [brands](../sys-mgmt/brands.md), which were previously called tenants.
::::

## About tenants

Starting with version 2024.2, authentik allows an administrator or operator to create multiple tenants. This means that an operator can manage several different and distinct authentik installations, each with it's own Install ID and license(s). The relationships between tenant and installation (Install ID) is a 1:1 relationship, so for each tenant, there is a unique Install ID.

::::danger
Expression policies currently have access to all tenants.
::::

The data for each tenant is stored in a separate PostgreSQL schema, providing full separation of user data. License data for the tenant is also stored in the schema.

Note that creating and managing multiple tenants is handled using authentik APIs, not in the Admin interface. For typical authentik installations in which only a single tenant is needed, the default tenant is automatically created by authentik, and does not need to be managed in the Admin interface.

### Licensing

For each additional tenant (beyond the default one), one or more licenses is required; a license key cannot be used for more than one tenant. Note that the license for the default tenant must be valid and up-to-date in order to create additional tenants.

A single tenant and its corresponding installation can have multiple license keys. For example, a company might purchase one license for 50 users, and then later in the same year need to buy another license for 50 more users, due to company growth. Both licenses are associated to the one installation, the one tenant.

Learn more in our documentation about [Enterprise licenses](../enterprise/manage-enterprise.mdx#license-management).

### Important considerations

- Upon creating another tenant, a new schema will be created by cloning the `template` schema. This special schema is like a tenant with no data created in it. Cloning an existing schema instead of creating a new one and running migrations on it is done for efficiency purposes.

- In a typical deployment, all data stored in Redis (such as tasks, locks, and cached objects) will have its keys prefixed by the `schema_name`.

- Files are isolated on a per-tenant basis, with each tenant folder named according to the schema_name. For example, `/media/t_example`. The same is true regardless of the storage backend.

- Using an [embedded outpost](../add-secure-apps/outposts/embedded/embedded.mdx) with multi-tenancy is not currently supported. Disable the embedded outpost with `AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true` configuration setting.

## Usage

To create one or more additional tenants (beyond the default tenant) use the following instructions.

### 1. Configure authentik to allow multiple tenants

First, enable the multi-tenancy feature with the `AUTHENTIK_TENANTS__ENABLED=true` [configuration setting](../install-config/configuration/configuration.mdx).

Next, set `AUTHENTIK_TENANTS__API_KEY` to a random string. This string will be used to authenticate to the tenancy API. This key allows the creation of recovery keys for every tenant hosted by authentik, so be sure to _store it securely_. Be aware that creating a recovery key allows access to all data stored inside a tenant.

Be sure to disable the embedded outpost with `AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true` because it is not supported with tenants.

### 2. Create a new tenant with authentik API endpoints

Tenants are created using the API routes associated. Search for `tenant` in the [API browser](../developer-docs/api/reference/authentik) for the available endpoints.

When creating a tenant you must specify a `name`, used for display purposes, and a `schema_name`, used to create the PostgreSQL schema associated with the tenant.

:::info
The `schema_name` must start with `t_` and not be more than 64 characters long.
:::

There is always at least one tenant, `public`. This is the default tenant and cannot be deleted. Despite its name, it is not freely available to the world. Instead, it is stored in the `public` schema of the PostgreSQL database.

### 3. Associate the new tenant with a domain

By default, all requests that do not explicitly belong to a tenant are redirected to the default tenant. Thus, after creating a tenant, you must associate a domain for which incoming requests will be redirected to said tenant.

You can do so with API endpoints. After creating a domain `example.org` that is associated to the tenant `t_example`, all requests made to `example.org` will use the `t_example` tenant. However, requests made to `authentik.tld`, `subdomain.example.org` and any other domain that is not associated with the `t_example` tenant will use the default tenant.

In summary, if you access a domain that is not explicitly associated with a specific tenant, it will be routed to the default tenant.
