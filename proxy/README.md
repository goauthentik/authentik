# passbook Proxy

[![CI Build status](https://img.shields.io/azure-devops/build/beryjuorg/passbook/3?style=flat-square)](https://dev.azure.com/beryjuorg/passbook/_build?definitionId=3)
![Docker pulls (proxy)](https://img.shields.io/docker/pulls/beryju/passbook-proxy.svg?style=flat-square)

Reverse Proxy based on [oauth2_proxy](https://github.com/oauth2-proxy/oauth2-proxy), completely managed and monitored by passbook.

## Usage

passbook Proxy is built to be configured by passbook itself, hence the only options you can directly give it are connection params.

The following environment variable are implemented:

`PASSBOOK_HOST`: Full URL to the passbook instance with protocol, i.e. "https://passbook.company.tld"

`PASSBOOK_TOKEN`: Token used to authenticate against passbook. This is generated after an Outpost instance is created.

`PASSBOOK_INSECURE`: This environment variable can optionally be set to ignore the SSL Certificate of the passbook instance. Applies to both HTTP and WS connections.

## Development

passbook Proxy uses an auto-generated API Client to communicate with passbook. This client is not kept in git. To generate the client locally, run `make generate`.

Afterwards you can build the proxy like any other Go project, using `go build`.
