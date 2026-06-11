---
title: Database seeding
sidebar_label: Database seeding
tags:
    - development
    - contributor
    - backend
---

Use the `seed_database` management command to add local development users, groups, memberships, applications, OAuth2 providers, entitlements, and group bindings to an authentik database.

The command only runs when `DEBUG` or `TEST` is enabled, and it requires `--ack-risk` so that it cannot be run accidentally. It is intended for local development and test data, not production systems.

## Seed a local database

Run the command from the project root after your development database has been migrated.

```shell
uv run python manage.py seed_database --ack-risk
```

By default, the command uses the `s` size preset and static mode. Static mode is repeatable: running the command again with the same options updates the same users, groups, providers, applications, and entitlements, and it does not create duplicate memberships or bindings.

To seed a larger dataset, choose a size preset.

```shell
uv run python manage.py seed_database --ack-risk --size m
```

The available presets are:

| Size |  Users | Groups | Superuser groups | Memberships per user | Applications | Entitlements per app | App group bindings per app |
| ---- | -----: | -----: | ---------------: | -------------------: | -----------: | -------------------: | -------------------------: |
| `s`  |     25 |      5 |                1 |                    2 |            5 |                    2 |                          2 |
| `m`  |    250 |     25 |                2 |                    3 |           25 |                    3 |                          3 |
| `l`  |  1,000 |    100 |                5 |                    5 |          100 |                    5 |                          5 |
| `xl` | 10,000 |    500 |               10 |                    8 |          250 |                    8 |                          8 |

You can override individual counts instead of using the preset values.

```shell
uv run python manage.py seed_database \
    --ack-risk \
    --users 100 \
    --groups 20 \
    --superuser-groups 2 \
    --memberships-per-user 3 \
    --apps 10 \
    --entitlements-per-app 2 \
    --app-group-bindings-per-app 2
```

For a tenant schema other than `public`, pass the tenant schema name.

```shell
uv run python manage.py seed_database --ack-risk --schema tenant1
```

## Static and random data

Static mode creates predictable names from the configured prefix:

- Users are named `ak-seed-user-000001`, `ak-seed-user-000002`, and so on.
- Groups are named `ak-seed-group-0001`, `ak-seed-group-0002`, and so on.
- Providers and applications are named from `ak-seed-provider-0001` and `ak-seed-app-0001`.
- Group memberships are assigned deterministically.

Random mode appends a generated run ID to the prefix and randomly assigns memberships. Use `--seed` to make random mode repeatable.

```shell
uv run python manage.py seed_database --ack-risk --mode random --seed 1234
```

Use `--prefix` to create a separate set of seed data.

```shell
uv run python manage.py seed_database --ack-risk --prefix my-feature
```

Generated users receive the password `ak-seed-password` unless you pass `--password`.

The command prints progress while each seed phase is applied. Use `--no-progress` to only print the final summary.
