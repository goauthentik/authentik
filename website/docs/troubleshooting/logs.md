---
title: Capturing logs
---

When troubleshooting issues it is useful to investigate the [event logs](../sys-mgmt/events/index.md) that are continuosuly outputted by authentik.

## Capturing Past Logs

The `--since` option can be used with both `docker logs` and `kubectl logs` commands. It can accept a Go durating string (e.g. `1m30s`, `3h`) or a specific date/time (e.g. `2006-01-02T07:00`, `2006-01-02`). When used, the command will output logs for the specified time period.

More information on this option and others can be found in the [`docker logs` command documentation](https://docs.docker.com/reference/cli/docker/container/logs/) and [`kubectl logs` command documentation](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/).

### Docker

To capture and display the logs of a Docker container in the terminal, use the following command:

```shell
docker logs <container_name_or_id> --timestamps --since 5m
```

### Kubernetes

To capture and display the logs from a pod deployed via Kubernetes, use the following command:

```shell
kubectl logs --timestamps --since 5m <pod_name>
```

## Continuously Capturing Logs

To continuously display logs from a Docker container or a pod deployed via Kubernetes, you can include the _follow_ option (`-f`, `--follow`). This option will stream logs into the terminal until stopped (`Ctrl + C` or closing the terminal).

### Docker

To stream the logs from a Docker container, use the following command:

```shell
docker logs <container_name_or_id> -f --timestamps
```

### Kubernetes Logs

To stream the logs from a pod deployed via Kubernetes, use the following command:

```shell
kubectl logs -f --timestamps <pod_name>
```
