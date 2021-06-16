---
title: Plex
---

Allows users to authenticate using their Plex credentials

## Preparation

None

## Authentik -> Sources

Add _Plex_ as a _source_

- Name: <Choose a name>
- Slug: Set a slug
- Client ID: Set a unique Client Id or leave the generated ID
- Press _Load Servers_ to login to plex and pick the authorized Plex Servers for "allowed users"
- Decide if *anyone* with a plex account can authenticate or only friends you share with

Save, and you now have Plex as a source.
  
:::note
To have the source appear on the default login page you must modify your Identification stage.  If you haven't customized the stages it is called _default-authentication-identification_
