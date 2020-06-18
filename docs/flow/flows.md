# Flows

Flows are a method of describing a sequence of stages. A stage represents a single verification or logic step. They are used to authenticate users, enroll them, and more.

Upon flow execution, a plan containing all stages is generated. This means that all attached policies are evaluated upon execution. This behaviour can be altered by enabling the `Re-evaluate Policies` option on the binding.

To determine which flow is linked, passbook searches all flows with the required designation and chooses the first instance the current user has access to.

## Permissions

Flows can have policies assigned to them. These policies determine if the current user is allowed to see and use this flow.

## Designation

Flows are designated for a single purpose. This designation changes when a flow is used. The following designations are available:

### Authentication

This is designates a flow to be used for authentication.

The authentication flow should always contain a `user_login` stage, which attaches the staged user to the current session.

### Invalidation

This designates a flow to be used to invalidate a session.

This stage should always contain a `user_logout` stage, which resets the current session.

### Enrollment

This designates a flow for enrollment. This flow can contain any amount of verification stages, such as email or captcha. At the end, to create the user, you can use the `user_write` stage, which either updates the currently staged user, or if none exists, creates a new one.

### Unenrollment

This designates a flow for unenrollment. This flow can contain any amount of verification stages, such as email or captcha. As a final stage, to delete the account, use the `user_delete` stage.

### Recovery

This designates a flow for recovery. This flow normally contains an `identification` stage to find the user. It can also contain any amount of verification stages, such as email or captcha.
Afterwards, use the `prompt` stage to ask the user for a new password and the `user_write` stage to update the password.

### Change Password

This designates a flow for password changes. This flow can contain any amount of verification stages, such as email or captcha.
Afterwards, use the `prompt` stage to ask the user for a new password and the `user_write` stage to update the password.
