---
title: Discord
---

Allows users to authenticate using their Discord credentials

## Preparation

You will need to create a Discord Application via the Discord Developer Portal.  


## Discord

1. Create an application in the Discord Developer Portal (This is Free) https://discord.com/developers/applications
2. Name the Application
3. 

## Authentik -> Sources

Add _Plex_ as a _source_

- Name: <Choose a name>
- Slug: Set a slug
- Client ID: Set a unique Client Id or leave the generated ID
- Press _Load Servers_ to login to plex and pick the authorized Plex Servers for "allowed users"
- Decide if *anyone* with a plex account can authenticate or only friends you share with

Save, and you now have Plex as a source.
