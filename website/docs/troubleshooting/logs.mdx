---
title: Capturing logs
---

When troubleshooting issues it is useful to investigate the [event logs](../sys-mgmt/events/index.md) that are continuosuly outputted by authentik.

## Enable `TRACE` or `DEBUG` modes

Both `TRACE` and `DEBUG` modes can be enabled so that authentik produces more detailed logs.

To enable `TRACE` mode:

<Tabs
groupId="platform"
defaultValue="docker-compose"
values={[
{label: 'docker-compose', value: 'docker-compose'},
{label: 'Kubernetes', value: 'kubernetes'},
]}>
<TabItem value="docker-compose">
Add the following block to your `.env` file:

```shell
AUTHENTIK_LOG_LEVEL=trace
```

Afterwards, run `docker compose up -d`.

  </TabItem>
  <TabItem value="kubernetes">
Add the following block to your `values.yml` file:

```yaml
authentik:
    log_level: trace
```

Afterwards, upgrade helm release.

  </TabItem>

To enable `DEBUGGING` mode:

<Tabs
groupId="platform"
defaultValue="docker-compose"
values={[
{label: 'docker-compose', value: 'docker-compose'},
{label: 'Kubernetes', value: 'kubernetes'},
]}>
<TabItem value="docker-compose">
Add the following block to your `.env` file:

```shell
AUTHENTIK_LOG_LEVEL=debug
```

Afterwards, run `docker compose up -d`.

  </TabItem>
  <TabItem value="kubernetes">
Add the following block to your `values.yml` file:

```yaml
authentik:
    log_level: debug
```

Afterwards, upgrade helm release.

  </TabItem>

## Capturing Past Logs

The `--since` option can be used with both `docker logs` and `kubectl logs` commands. It can accept a Go durating string (e.g. `1m30s`, `3h`) or a specific date/time (e.g. `2006-01-02T07:00`, `2006-01-02`). When used, the command will output logs for the specified time period.

More information on this option and others can be found in the [`docker logs` command documentation](https://docs.docker.com/reference/cli/docker/container/logs/) and [`kubectl logs` command documentation](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/).

### Docker

To capture and display the logs of a Docker container in the terminal, use the following command:

```shell
docker logs <container_name_or_id> --since 5m
```

### Kubernetes

To capture and display the logs from a pod deployed via Kubernetes, use the following command:

```shell
kubectl logs --since 5m <pod_name>
```

## Continuously Capturing Logs

To continuously display logs from a Docker container or a pod deployed via Kubernetes, you can include the _follow_ option (`-f`, `--follow`). This option will stream logs into the terminal until stopped (`Ctrl + C` or closing the terminal).

### Docker

To stream the logs from a Docker container, use the following command:

```shell
docker logs <container_name_or_id> -f
```

### Kubernetes Logs

To stream the logs from a pod deployed via Kubernetes, use the following command:

```shell
kubectl logs -f <pod_name>
```
