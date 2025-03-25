---
title: Capturing logs
---

To capture logs from a docker container, you can run the command below to output logs into the terminal

```shell
docker logs <container_name_or_id> --timestamps --since 5m
```

This command will output logs from the specified container for the last 5 minutes.

The `--since` option is flexible and can accept a Go durating string (e.g. `1m30s`, `3h`) or a specific date/time (e.g. `2006-01-02T07:00`, `2006-01-02`).

More information can be found in the `docker logs` command documentation here: *https://docs.docker.com/reference/cli/docker/container/logs/*
