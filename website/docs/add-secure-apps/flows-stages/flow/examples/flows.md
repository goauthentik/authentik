---
title: Example flows
---

:::info
You can apply these flows multiple times to stay updated, however this will discard all changes you've made.
:::

:::info
The example flows provided below will **override** the default flows, please review the contents of the example flow before importing and consider exporting the affected existing flows first.
:::

These example flow blueprints are bundled with authentik. To import one, open the authentik Admin interface, navigate to **Flows and Stages** > **Flows**, click **Import**, select **Local path**, and choose the blueprint path shown below. You can also download the blueprint manually and import it with **File upload**.

## Enrollment (2 Stage)

Blueprint path: `example/flows-enrollment-2-stage.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-enrollment-2-stage.yaml">here</DownloadLink> and save the file.

Sign-up flow for new users, which prompts them for their username, email, password and name. No verification is done. Users are also immediately logged on after this flow.

## Enrollment with email verification

Blueprint path: `example/flows-enrollment-email-verification.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-enrollment-email-verification.yaml">here</DownloadLink> and save the file.

Same flow as above, with an extra email verification stage.

You'll probably have to adjust the Email stage and set your connection details.

## Two-factor Login

Blueprint path: `example/flows-login-2fa.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-login-2fa.yaml">here</DownloadLink> and save the file.

Login flow which follows the default pattern (username/email, then password), but also checks for the user's OTP token, if they have one configured.

You can force two-factor authentication by editing the _Not configured action_ in the Authenticator Validation Stage.

## Login with conditional Captcha

Blueprint path: `example/flows-login-conditional-captcha.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-login-conditional-captcha.yaml">here</DownloadLink> and save the file.

Login flow which conditionally shows the users a captcha, based on the reputation of their IP and Username.

By default, the captcha test keys are used. You can get a proper key [here](https://www.google.com/recaptcha/intro/v3.html).

## Recovery with email and MFA verification

Blueprint path: `example/flows-recovery-email-mfa-verification.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-recovery-email-mfa-verification.yaml">here</DownloadLink> and save the file.

With this recovery flow, the user is sent an email after they've identified themselves. After they click on the link in the email, they will have to verify their configured MFA device, and are prompted for a new password and immediately logged on.

There's also <DownloadLink to="/blueprints/example/flows-recovery-email-verification.yaml">a version</DownloadLink> of this flow available without MFA validation at `example/flows-recovery-email-verification.yaml`, which is not recommended.

## User deletion

Blueprint path: `example/flows-unenrollment.yaml`

Flow: right-click <DownloadLink to="/blueprints/example/flows-unenrollment.yaml">here</DownloadLink> and save the file.

Flow for users to delete their account.

:::warning
This is done without any warning.
:::
