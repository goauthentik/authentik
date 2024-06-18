---
title: Overview
---

Flows are a method of describing a sequence of stages. A stage represents a single verification or logic step. They are used to authenticate users, enroll them, and more.

For example, a standard login flow would consist of the following stages:

-   Identification, user identifies themselves via a username or email address
-   Password, the user's password is checked against the hash in the database
-   Log the user in

Upon flow execution, a plan containing all stages is generated. This means that all attached policies are evaluated upon execution. This behaviour can be altered by enabling the **Evaluate when stage is run** option on the binding.

The determine which flow should be used, authentik will first check which default authentication flow is configured in the active [**Brand**](../core/brands.md). If no default is configured there, the policies in all flows with the matching designation are checked, and the first flow with matching policies sorted by `slug` will be used.

## Permissions

Flows can have policies assigned to them. These policies determine if the current user is allowed to see and use this flow.

Keep in mind that in certain circumstances, policies cannot match against users and groups as there is no authenticated user yet.

### Denied action

Configure what happens when access to a flow is denied by a policy. By default, authentik will redirect to a `?next` parameter if set, and otherwise show an error message.

-   `MESSAGE_CONTINUE`: Show a message if no `?next` parameter is set, otherwise redirect.
-   `MESSAGE`: Always show error message.
-   `CONTINUE`: Always redirect, either to `?next` if set, otherwise to the default interface.

## Designation

Flows are designated for a single purpose. This designation changes when a flow is used. The following designations are available:

#### Authentication

This is designates a flow to be used for authentication.

The authentication flow should always contain a [**User Login**](stages/user_login/index.md) stage, which attaches the staged user to the current session.

#### Invalidation

This designates a flow to be used to invalidate a session.

This flow should always contain a [**User Logout**](stages/user_logout.md) stage, which resets the current session.

#### Enrollment

This designates a flow for enrollment. This flow can contain any amount of verification stages, such as [**email**](stages/email/) or [**captcha**](stages/captcha/). At the end, to create the user, you can use the [**user_write**](stages/user_write.md) stage, which either updates the currently staged user, or if none exists, creates a new one.

#### Unenrollment

This designates a flow for unenrollment. This flow can contain any amount of verification stages, such as [**email**](stages/email/) or [**captcha**](stages/captcha/). As a final stage, to delete the account, use the [**user_delete**](stages/user_delete.md) stage.

#### Recovery

This designates a flow for recovery. This flow normally contains an [**identification**](stages/identification/) stage to find the user. It can also contain any amount of verification stages, such as [**email**](stages/email/) or [**captcha**](stages/captcha/).
Afterwards, use the [**prompt**](stages/prompt/) stage to ask the user for a new password and the [**user_write**](stages/user_write.md) stage to update the password.

#### Stage configuration

This designates a flow for general setup. This designation doesn't have any constraints in what you can do. For example, by default this designation is used to configure Factors, like change a password and setup TOTP.

## Import & Export

Flows can be imported and exported to share with other people, the community and for troubleshooting. Flows can be imported to apply new functionality and apply existing workflows.

Download our [Example flows](./examples/flows.md) and then import them into your authentik instance.

Starting with authentik 2022.8, flows will be exported as YAML, but JSON-based flows can still be imported.

## Behavior settings

### Compatibility mode

The compatibility mode increases compatibility with password managers. Password managers like [1Password](https://1password.com/) for example don't need this setting to be enabled, when accessing the flow from a desktop browser. However accessing the flow from a mobile device might necessitate this setting to be enabled.

The technical reasons for this settings' existence is due to the JavaScript libraries we're using for the default flow interface. These interfaces are implemented using [Lit](https://lit.dev/), which is a modern web development library. It uses a web standard called ["Shadow DOMs"](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM), which makes encapsulating styles simpler. Due to differences in Browser APIs, many password managers are not compatible with this technology.

When the compatibility mode is enabled, authentik uses a polyfill which emulates the Shadow DOM APIs without actually using the feature, and instead a traditional DOM is rendered. This increases support for password managers, especially on mobile devices.
