---
title: Consent stage
authentik_version: "2024.4"
authentik_enterprise: true
---

The Consent stage is used to configure the authorization server (authentik) to prompt the user for consent to share data with the relying party (RP), the application the user is logging in to.

## Example use case

This stage can be used to leverage an external OAuth source, and allow users logging into to select that authentik can provide login data to the application you are logging in to.

## Considerations

TODO

## Consent stage workflow

insert mermaid diagram here

## Create and configure a Consent stage

How to create it, the three modes, etc. (this is how you can set it to expire)...

you have to create an Expression policy to bind to the stage (go to the Flow, go to Stage bindings tab, click on carot beside the stage to expand it, then bind the policy there. (Note to users about the policy is bound to the stage WITHIN this flow... not to the Stage as a whole!!))

This stage has three modes:

1. Always require (the user will see message and consent by clicking Continue
2. Permanent: saves fact that you clicked on Continue, cretes a Consent object with alink to the user and to the app,, and stores which data (but not value),
3. Expiring: means you have to click Continue anytime after the expery date stage set in stage as Duration.
