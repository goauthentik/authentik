---
title: Errors when uploading icons
---

There are two common causes for icon and image upload problems when authentik uses local file storage.

## 1. Permissions problems

:::info
This section applies to Docker Compose and other deployments that use bind mounts, where host filesystem permissions determine whether authentik can write to the mounted data directory.
:::

This issue is most likely caused by permissions. Docker creates bound volumes as root, but the authentik processes do not run as root.

This will cause issues with icon uploads (for Applications), background uploads (for Flows) and local backups.

For Docker Compose, run these commands in the directory of your Compose file:

```shell
sudo chown 1000:1000 data/
sudo chown 1000:1000 custom-templates/
sudo chmod ug+rwx data/
sudo chmod ug+rx certs/
```

Alternatively, If you are using Kubernetes, ensure that the volume mounted at `/data` is writable by the authentik container.

## 2. Legacy `/media` mounts after upgrading

If you upgraded from an older release and existing files still appear, but the upload controls are missing in **Customization** > **Files**, or you cannot upload new files, check your local storage mount path.

Current authentik versions expect local file storage at `/data`, with media files stored under `/data/media`. A legacy mount to `/media` will still allow older files to be read through compatibility handling, while preventing new uploads and file management.

Update your deployment to use the current storage layout.

Examples:

```yaml
# Docker Compose
volumes:
    - ./data:/data
    - ./data/custom-templates:/templates
```

For Kubernetes deployments, mount your persistent storage at `/data` instead of `/media`.

If you previously stored files under a path mounted to `/media`, move that data so it is available under `/data/media` inside the authentik container.
