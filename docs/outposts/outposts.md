# Outposts

An outpost is a single deployment of a passbook component, which can be deployed in a completely separate environment. Currently, only the Proxy Provider is supported as outpost.

![](outposts.png)

Upon creation, a service account and a token is generated. The service account only has permissions to read the outpost and provider configuration. This token is used by the Outpost to connect to passbook.

To deploy an outpost, see: <a name="deploy">

- [Kubernetes](deploy-kubernetes.md)
- [docker-compose](deploy-docker-compose.md)

In future versions, this snippet will be automatically generated. You will also be able to deploy an outpost directly into a kubernetes cluster.
