# Flows

Flows are a method of describing a sequence of stages. A stage represents a single verification or logic step. They are used to authenticate users, enroll them, and more.

Upon Flow execution, a plan is generated, which contains all stages. This means upon execution, all attached policies are evaluated. This behaviour can be altered by enabling the `Re-evaluate Policies` option on the binding.

To determine which flow is linked, passbook searches all Flows with the required designation and chooses the first instance the current user has access to.

## Permissions

Flows can have policies assigned to them, which determines if the current user is allowed to see and use this flow.

## Designation

Flows are designated for a single Purpose. This designation changes when a Flow is used. The following designations are available:

### Authentication

This is designates a flow to be used for authentication.

The authentication flow should always contain a `user_login` stage, which attaches the staged user to the current session.

### Invalidation

This designates a flow to be used for the invalidation of a session.

This stage should always contain a `user_logout` stage, which resets the current session.

### Enrollment

This designates a flow for enrollment. This flow can contain any amount of Prompt stages, E-Mail verification or Captchas. At the end to create the user, you can use the `user_write` stage, which either updates the currently staged user, or if none exists, creates a new one.

### Unenrollment

This designates a flow for unenrollment. This flow can contain any amount of verification, like `email` or captcha. To finally delete the account, use the `user_delete` stage.

### Recovery

This designates a flow for recovery. This flow normally contains an `identification` stage to find the user. Then it can contain any amount of verification, like `email` or captcha.
Afterwards, use the `prompt` stage to ask the user for a new password and use `user_write` to update the password.

### Change Password

This designates a flow for password changing. This flow can contain any amount of verification, like `email` or captcha.
Afterwards, use the `prompt` stage to ask the user for a new password and use `user_write` to update the password.
