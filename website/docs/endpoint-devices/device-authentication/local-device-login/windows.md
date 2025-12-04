---
title: Windows local device login
sidebar_label: Windows
tags: [authentik Agent, device login, device authentication, windows credential provider, wcp]
---

## Windows (Windows Credential Provider)

Windows Credential Provider is a component of the authentik Agent that allows logging in to Windows workstations using authentik credentials.

It currently only supports local login; RDP login is not supported.

:::warning

- WCP is only tested on Windows 11 and Windows Server 2022.
- When WCP is enabled, the password of the Windows user account that's used is set to a random string.
- WCP can cause issues with user encrypted directories.
- Support with Active directory has not been confirmed yet.
  :::
