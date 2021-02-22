<img src="https://goauthentik.io/img/icon_top_brand_colour.svg" height="250" alt="authentik logo">

---

[![](https://img.shields.io/discord/809154715984199690?label=Discord&style=flat-square)](https://discord.gg/KPnmtNWy)
[![CI Build status](https://img.shields.io/azure-devops/build/beryjuorg/authentik/1?style=flat-square)](https://dev.azure.com/beryjuorg/authentik/_build?definitionId=1)
[![Tests](https://img.shields.io/azure-devops/tests/beryjuorg/authentik/1?compact_message&style=flat-square)](https://dev.azure.com/beryjuorg/authentik/_build?definitionId=1)
[![Code Coverage](https://img.shields.io/codecov/c/gh/beryju/authentik?style=flat-square)](https://codecov.io/gh/BeryJu/authentik)
![Docker pulls](https://img.shields.io/docker/pulls/beryju/authentik.svg?style=flat-square)
![Latest version](https://img.shields.io/docker/v/beryju/authentik?sort=semver&style=flat-square)
![LGTM Grade](https://img.shields.io/lgtm/grade/python/github/BeryJu/authentik?style=flat-square)

## What is authentik?

authentik is an open-source Identity Provider focused on flexibility and versatility. You can use authentik in an existing environment to add support for new protocols. authentik is also a great solution for implementing signup/recovery/etc in your application, so you don't have to deal with it.

## Installation

For small/test setups it is recommended to use docker-compose, see the [documentation](https://goauthentik.io/docs/installation/docker-compose/)

For bigger setups, there is a Helm Chart in the `helm/` directory. This is documented [here](https://goauthentik.io/docs/installation/kubernetes/)

## Screenshots

![](https://goauthentik.io/img/screen_apps.png)
![](https://goauthentik.io/img/screen_admin.png)

## Development

See [Development Documentation](https://goauthentik.io/docs/development/local-dev-environment)

## Security

See [SECURITY.md](SECURITY.md)
