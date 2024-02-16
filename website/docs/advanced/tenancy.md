---
title: Tenancy
---

<span class="badge badge--primary">Enterprise</span>

---

::::warning
This feature is in alpha. Use at your own risk.
::::

::::info
This feature is available from 2024.2 and is not to be confused with [brands](../core/brands.md), which were previously called tenants.
::::

## About tenants

Starting with version 2024.2, authentik allows an administrator or operator to create multiple tenants. This means that an operator can manage several different and distinct authentik installations, each with it's own Install ID and license(s).

The data for each tenant is stored in a separate PostgreSQL schema, providing full separation of user data. License data for the tenant is also stored in the schema.

Note that creating and managing multiple tenants is handled using authentik APIs, not in the Admin interface. For typical authentik installations in which only a single tenant is needed, the default tenant is deployed and used, and does not need to be managed in the Admin interface.

For each additional tenant (beyond the default one), one or more licenses is required; a license key cannot be used for more than one tenant. The relationships between tenant and installation (Install ID) is a 1:1 relationship, so for each tenant, there is a unique Install ID.

A single tenant and its installation can have multiple license keys. For example, a company might purchase one license for 50 users, and then later in the same year need to buy another license for 50 more users, due to company growth. Both licenses are associated to the one installation, the one tenant.

## Usage

The multi-tenants feature must be enabled with the `AUTHENTIK_TENANTS__ENABLED=true`[configuration setting](../installation/configuration.mdx).

You also need to set `AUTHENTIK_TENANTS__API_KEY` to a random string, which will be used to authenticate to the tenancy API. This key allows the creation of recovery keys for every tenant hosted by authentik, so be sure to store it securely.

:::info
You will also need to disable the embedded outpost with `AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true` because it is not supported with tenants.
:::

Tenants are created using the API routes associated. Search for `tenant` in the [API browser](../../developer-docs/api/) for the available endpoints.

When creating a tenant, you must specify a `name`, used for display purposes, and a `schema_name`, used to create the PostgreSQL schema associated with the tenant. That `schema_name` must start with `t_` and not be more than 64 characters long.

There is always at least one tenant, `public`. This is the default tenant and cannot be deleted. Despite its name, it is not freely available to the world. Instead, it is stored in the `public` schema of the PostgreSQL database.

By default, all requests that do not explicitly belong to a tenant are redirected to the default tenant. Thus, after creating a tenant, you must associate a domain for which incoming requests will be redirected to said tenant. You can do so with API endpoints. After creating a domain `example.org` that is associated to the tenant `t_example`, all requests made to `example.org` will use the `t_example` tenant. However, requests made to `authentik.tld`, `subdomain.example.org` and any other domain that is not associated with the `t_example` tenant will use the default tenant.

In summary, if you access a domain that is not explicitly associated with a specific tenant, it will be routed to the default tenant.

::::warning
Expression policies currently have access to all tenants.
::::

## Notes

Upon creating another tenant, a new schema will be created by cloning the `template` schema. This special schema is like a tenant with no data created in it. Cloning an existing schema instead of creating a new one and running migrations on it is done for efficiency purposes.

Data stored in Redis (cache, tasks, locks) will usually get its keys prefixed by the `schema_name`.

Files are stored by-tenant, under a `schema_name` directory. For example, `/media/t_example`. The same is true regardless of the storage backend.
