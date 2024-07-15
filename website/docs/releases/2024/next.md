---
title: Release 2024.next
slug: "/releases/2024.next"
---

:::::note
2024.next has not been released yet! We're publishing these release notes as a preview of what's to come, and for our awesome beta testers trying out release candidates.

To try out the release candidate, replace your Docker image tag with the latest release candidate number, such as 2024.next.0-rc1. You can find the latest one in [the latest releases on GitHub](https://github.com/goauthentik/authentik/releases). If you don't find any, it means we haven't released one yet.
:::::

## Breaking changes

### Action is required

-   **LDAP property mappings simplification**

    LDAP property mappings have been reworked to remove **Object field**. With this release, instead of returning a single user or group attribute for each property mapping, you can now return several of them. Here is an example of what new property mappings look like:

    ```python
    return {
        "username": ldap.get("uid"), # list_flatten is automatically applied to top-level attributes
        "attributes": {
            "phone": list_flatten(ldap.get("phoneNumber")), # but not for attributes!
        },
    }
    ```

    This property mapping populates the `username` and `attributes.phone` attributes of a user at the same time, reducing the number of mappings that are run and thus improving performance. Additionally, they are more straightforward to read, and this change allowed us to implement property mappings for OAuth and SAML sources as well.

    authentik will automatically migrate existing property mappings to this new format, by generating some Python code for each of the existing property mappings expressions. authentik-manager property mappings will automatically get updated to the new format.

    **If you have any custom property mappings, we recommend migrating them to this new format.**

## New features

## Upgrading

This release does not introduce any new requirements.

### docker-compose

To upgrade, download the new docker-compose file and update the Docker stack with the new version, using these commands:

```shell
wget -O docker-compose.yml https://goauthentik.io/version/xxxx.x/docker-compose.yml
docker compose up -d
```

The `-O` flag retains the downloaded file's name, overwriting any existing local file with the same name.

### Kubernetes

Upgrade the Helm Chart to the new version, using the following commands:

```shell
helm repo update
helm upgrade authentik authentik/authentik -f values.yaml --version ^xxxx.x
```

## Minor changes/fixes

<!-- _Insert the output of `make gen-changelog` here_ -->

## API Changes

<!-- _Insert output of `make gen-diff` here_ -->
