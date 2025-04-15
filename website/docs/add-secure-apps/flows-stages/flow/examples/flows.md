---
title: Example flows
---

:::info
You can apply these flows multiple times to stay updated, however this will discard all changes you've made.
:::

:::info
The example flows provided below will **override** the default flows, please review the contents of the example flow before importing and consider exporting the affected existing flows first.
:::

## Enrollment (2 Stage)

Flow: right-click [here](/blueprints/example/flows-enrollment-2-stage.yaml) and save the file.

Sign-up flow for new users, which prompts them for their username, email, password and name. No verification is done. Users are also immediately logged on after this flow.

## Enrollment with email verification

Flow: right-click [here](/blueprints/example/flows-enrollment-email-verification.yaml) and save the file.

Same flow as above, with an extra email verification stage.

You'll probably have to adjust the Email stage and set your connection details.

## Two-factor Login

Flow: right-click [here](/blueprints/example/flows-login-2fa.yaml) and save the file.

Login flow which follows the default pattern (username/email, then password), but also checks for the user's OTP token, if they have one configured.

You can force two-factor authentication by editing the _Not configured action_ in the Authenticator Validation Stage.

## Login with conditional Captcha

Flow: right-click [here](/blueprints/example/flows-login-conditional-captcha.yaml) and save the file.

Login flow which conditionally shows the users a captcha, based on the reputation of their IP and Username.

By default, the captcha test keys are used. You can get a proper key [here](https://www.google.com/recaptcha/intro/v3.html).

## Recovery with email verification

Flow: right-click [here](https://version-2024-12.goauthentik.io/assets/files/flows-recovery-email-verification-408d6afeff2fbf276bf43a949e332ef6.yaml) and save the file.

Recovery flow, the user is sent an email after they've identified themselves. After they click on the link in the email, they are prompted for a new password and immediately logged on.

## User deletion

Flow: right-click [here](/blueprints/example/flows-unenrollment.yaml) and save the file.

Flow for users to delete their account.

:::warning
This is done without any warning.
:::
