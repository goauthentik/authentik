---
title: Password Policy
tags:
    - policy
    - password
    - security
---

Use a Password policy when you want to validate a password entered in a prompt stage.

This policy is most often attached to a [Prompt stage](../../../add-secure-apps/flows-stages/stages/prompt/index.md) through that stage's **Validation Policies**.

## What it can enforce

A Password policy can enforce:

- minimum length
- minimum counts for uppercase, lowercase, digits, and symbols
- a custom symbol set
- [Have I Been Pwned](https://haveibeenpwned.com/) exposure checks
- [zxcvbn](https://github.com/dropbox/zxcvbn) strength checks

The policy reads the configured password field from prompt data, so the field key in the policy must match the password field used by your prompt stage.

:::warning Password Guidance
By default, authentik's Password policy aligns with [NIST password guidance](https://pages.nist.gov/800-63-4/sp800-63b.html#password). Be careful when tightening or weakening those defaults. For broader guidance, see [Hardening authentik](../../../security/security-hardening.md#password-policy).
:::

## Have I Been Pwned checks

When the HIBP check is enabled, authentik compares the password hash against the Have I Been Pwned password database.

Only the first 5 characters of the SHA-1 hash are sent to the API. The remaining comparison is done in authentik.

## zxcvbn checks

When the zxcvbn check is enabled, authentik evaluates password strength and can reject passwords that are still weak even if they satisfy simple character-count rules.

## Create a Password policy

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy** and select **Password Policy**.
4. Configure the password field and validation rules you want to enforce.
5. Click **Create Policy**.

## Attach it to password entry

In most cases, bind the policy to the prompt stage where the user enters a new password.

This is commonly used in:

- enrollment flows
- password reset flows
- password change flows

If you also want to prevent password reuse, combine this policy with [Password Uniqueness Policy](./password-uniqueness.md).
