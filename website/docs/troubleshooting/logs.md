---
title: Capturing logs
---

## Docker logs

### Capturing Past Logs

To capture logs from a docker container, you can run the command below to output logs into the terminal:

```shell
docker logs <container_name_or_id> --timestamps --since 5m
```

This command will output logs from the specified container for the last 5 minutes.

:::note
The `--since` option is flexible and can accept a Go durating string (e.g. `1m30s`, `3h`) or a specific date/time (e.g. `2006-01-02T07:00`, `2006-01-02`).
More information on this option and others can be found in the `docker logs` command documentation here: *https://docs.docker.com/reference/cli/docker/container/logs/*
:::

### Continuously Capturing Logs

To continuously output logs from a docker container, you can include the _follow_ option (`-f`, `--follow`):

```shell
docker logs <container_name_or_id> -f --timestamps
```

This command will stream logs into the terminal until stopped.


## Kubernetes Logs

### Capturing Past Logs

To capture logs from a container deployed via kubernetes, you can run the command below to output logs into the terminal:

```shell
kubectl logs --since 5m <pod_name_or_id>/<container_name_or_id>
```

This command will output logs from the specified container for the last 5 minutes.

:::note
The `--since` option is flexible and can accept a Go durating string (e.g. `1m30s`, `3h`) or a specific date/time (e.g. `2006-01-02T07:00`, `2006-01-02`).
More information on this option and others can be found in the `kubectl logs` command documentation here: *https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/*
:::

### Continuously Capturing Logs

To continuously output logs from a container deployed via kubernetes, you can include the _follow_ option (`-f`, `--follow`):

```shell
kubectl logs -f <pod_name_or_id>/<container_name_or_id>
```

This command will stream logs into the terminal until stopped.
