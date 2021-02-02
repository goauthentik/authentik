# authentik outpost

[![CI Build status](https://img.shields.io/azure-devops/build/beryjuorg/authentik/3?style=flat-square)](https://dev.azure.com/beryjuorg/authentik/_build?definitionId=3)
![Docker pulls (proxy)](https://img.shields.io/docker/pulls/beryju/authentik-proxy.svg?style=flat-square)

Reverse Proxy based on [oauth2_proxy](https://github.com/oauth2-proxy/oauth2-proxy), completely managed and monitored by authentik.

## Usage

authentik Proxy is built to be configured by authentik itself, hence the only options you can directly give it are connection params.

The following environment variable are implemented:

`AUTHENTIK_HOST`: Full URL to the authentik instance with protocol, i.e. "https://authentik.company.tld"

`AUTHENTIK_TOKEN`: Token used to authenticate against authentik. This is generated after an Outpost instance is created.

`AUTHENTIK_INSECURE`: This environment variable can optionally be set to ignore the SSL Certificate of the authentik instance. Applies to both HTTP and WS connections.

## Development

authentik Proxy uses an auto-generated API Client to communicate with authentik. This client is not kept in git. To generate the client locally, run `make generate`.

Afterwards you can build the proxy like any other Go project, using `go build`.
