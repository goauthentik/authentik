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

See https://developers.cloudflare.com/turnstile/get-started/migrating-from-recaptcha.

#### Configuration options

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **Create**.
3. Select **Captcha Stage** and click **Next**.
4. Provide a descriptive name for the stage (e.g. `authentication-captcha`) and configure the following required settings based on the values of your [Cloudflare Turnstile Widget](https://developers.cloudflare.com/turnstile/concepts/widget/):
    - Under **Stage-specific settings**:
        - **Public Key**: set to the **Turnstile Site Key** value from the widget.
        - **Private Key**: set to the **Turnstile Secret Key** value from the widget.
        - **Enable Interactive**: Enable this option if the Turnstile instance is configured as **Invisible** or **Managed**.
        - Leave both score thresholds at their default, as they are not supported for Turnstile.

- JS URL: `https://challenges.cloudflare.com/turnstile/v0/api.js`
- API URL: `https://challenges.cloudflare.com/turnstile/v0/siteverify`

**Score options do not apply when using with turnstile**
