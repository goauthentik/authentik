---
title: Captcha stage
---

This stage adds a form of verification using [Google's reCAPTCHA](https://www.google.com/recaptcha/intro/v3.html) or compatible services.

Currently supported implementations:

- [Google reCAPTCHA](#google-recaptcha)
- [hCaptcha](#hcaptcha)
- [Cloudflare Turnstile](#cloudflare-turnstile)

## Captcha provider configuration

### Google reCAPTCHA

This stage has two required fields: Public key and private key. These can both be acquired at https://www.google.com/recaptcha/admin.

![](./captcha-admin.png)

#### Configuration options

- Interactive: Enabled when using reCAPTCHA v3
- Score minimum threshold: `0.5`
- Score maximum threshold: `1`
- JS URL: `https://www.recaptcha.net/recaptcha/api.js`
- API URL: `https://www.recaptcha.net/recaptcha/api/siteverify`

### hCaptcha

See https://docs.hcaptcha.com/switch

#### Configuration options

- Interactive: Enabled
- JS URL: `https://js.hcaptcha.com/1/api.js`
- API URL: `https://api.hcaptcha.com/siteverify`

**Score options only apply to hCaptcha Enterprise**

- Score minimum threshold: `0`
- Score maximum threshold: `0.5`

### Cloudflare Turnstile

See https://developers.cloudflare.com/turnstile/get-started/migrating-from-recaptcha

#### Configuration options

In authentik open the Admin interface and navigate to Flows and Stages --> Stages --> Create
Select Captcha Stage and press Next
Name the stage e.g. authentication-captcha
Under the Stage-specific settings copy the following from the Cloudflare Turnstile Widget you setup previously
- Copy the Turnstile Site Key to the Public Key
- Copy the Turnstile Site Key to the Private Key
- Enable Interactive: Enabled if the Turnstile instance is configured as visible or managed
- Leave both score thresholds at their default, they are not used for Turnstile
- JS URL: `https://challenges.cloudflare.com/turnstile/v0/api.js`
- API URL: `https://challenges.cloudflare.com/turnstile/v0/siteverify`

**Score options do not apply when using with turnstile**
