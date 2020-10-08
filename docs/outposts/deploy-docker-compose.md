# Outpost deployment in docker-compose

To deploy an outpost with docker-compose, use  this snippet in your docker-compose file.

You can also run the outpost in a separate docker-compose project, you just have to ensure that the outpost container can reach your application container.

```yaml
version: '3.5'

services:
  passbook_proxy:
    image: beryju/passbook-proxy:0.10.0-stable
    ports:
      - 4180:4180
      - 4443:4443
    environment:
      PASSBOOK_HOST: https://your-passbook.tld
      PASSBOOK_INSECURE: 'false'
      PASSBOOK_TOKEN: token-generated-by-passbook
```
