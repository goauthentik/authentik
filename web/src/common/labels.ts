import {
    Device,
    DeviceChallenge,
    DeviceClassesEnum,
    EventActions,
    IntentEnum,
    SeverityEnum,
    UserTypeEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";

/* Various tables in the API for which we need to supply labels */

export const intentEnumToLabel = new Map<IntentEnum, string>([
    [IntentEnum.Api, msg("API Access")],
    [IntentEnum.AppPassword, msg("App password")],
    [IntentEnum.Recovery, msg("Recovery")],
    [IntentEnum.Verification, msg("Verification")],
    [IntentEnum.UnknownDefaultOpenApi, msg("Unknown intent")],
]);

export const intentToLabel = (intent: IntentEnum) => intentEnumToLabel.get(intent);

export const eventActionToLabel = new Map<EventActions | undefined, string>([
    [EventActions.Login, msg("Login")],
    [EventActions.LoginFailed, msg("Failed login")],
    [EventActions.Logout, msg("Logout")],
    [EventActions.UserWrite, msg("User was written to")],
    [EventActions.SuspiciousRequest, msg("Suspicious request")],
    [EventActions.PasswordSet, msg("Password set")],
    [EventActions.SecretView, msg("Secret was viewed")],
    [EventActions.SecretRotate, msg("Secret was rotated")],
    [EventActions.InvitationUsed, msg("Invitation used")],
    [EventActions.AuthorizeApplication, msg("Application authorized")],
    [EventActions.SourceLinked, msg("Source linked")],
    [EventActions.ImpersonationStarted, msg("Impersonation started")],
    [EventActions.ImpersonationEnded, msg("Impersonation ended")],
    [EventActions.FlowExecution, msg("Flow execution")],
    // These are different: look closely.
    [EventActions.PolicyExecution, msg("Policy execution")],
    [EventActions.PolicyException, msg("Policy exception")],
    [EventActions.PropertyMappingException, msg("Property Mapping exception")],
    // These are different: look closely.
    [EventActions.SystemTaskExecution, msg("System task execution")],
    [EventActions.SystemTaskException, msg("System task exception")],
    [EventActions.SystemException, msg("General system exception")],
    [EventActions.ConfigurationError, msg("Configuration error")],
    [EventActions.ModelCreated, msg("Model created")],
    [EventActions.ModelUpdated, msg("Model updated")],
    [EventActions.ModelDeleted, msg("Model deleted")],
    [EventActions.EmailSent, msg("Email sent")],
    [EventActions.UpdateAvailable, msg("Update available")],
]);

export const actionToLabel = (action?: EventActions): string =>
    eventActionToLabel.get(action) ?? action ?? "";

export const severityEnumToLabel = new Map<SeverityEnum | null | undefined, string>([
    [SeverityEnum.Alert, msg("Alert")],
    [SeverityEnum.Notice, msg("Notice")],
    [SeverityEnum.Warning, msg("Warning")],
]);

export const severityToLabel = (severity: SeverityEnum | null | undefined) =>
    severityEnumToLabel.get(severity) ?? msg("Unknown severity");

export function severityToLevel(severity?: SeverityEnum | null): string {
    switch (severity) {
        case SeverityEnum.Warning:
            return "pf-m-warning";
        case SeverityEnum.Alert:
            return "pf-m-danger";
    }
    return "pf-m-info";
}

/**
 * @todo Add verbose_name field to now vendored OTP devices
 * @todo We seem to have these constants in the `ModelEnum` object in lowercase.
 */
export const deviceTypeToLabel = new Map<string, string>([
    ["authentik_stages_authenticator_static.StaticDevice", msg("Static tokens")],
    ["authentik_stages_authenticator_totp.TOTPDevice", msg("TOTP Device")],
]);

export const deviceTypeName = (device: Device) =>
    deviceTypeToLabel.get(device.type) ?? device?.verboseName ?? "";

export function formatDeviceChallengeMessage(deviceChallenge?: DeviceChallenge | null): string {
    switch (deviceChallenge?.deviceClass) {
        case DeviceClassesEnum.Email: {
            const { email } = deviceChallenge.challenge;

            return email
                ? msg(str`A code has been sent to your address: ${email}`)
                : msg("A code has been sent to your email address.");
        }
        case DeviceClassesEnum.Sms:
            return msg("A one-time use code has been sent to you via SMS text message.");
        case DeviceClassesEnum.Totp:
            return msg("Open your authenticator app to retrieve a one-time use code.");
        case DeviceClassesEnum.Static:
            return msg("Enter a one-time recovery code for this user.");
    }

    return msg("Enter the code from your authenticator device.");
}

const _userTypeToLabel = new Map<UserTypeEnum | undefined, string>([
    [UserTypeEnum.Internal, msg("Internal")],
    [UserTypeEnum.External, msg("External")],
    [UserTypeEnum.ServiceAccount, msg("Service account")],
    [UserTypeEnum.InternalServiceAccount, msg("Service account (internal)")],
]);

export const userTypeToLabel = (type?: UserTypeEnum): string =>
    _userTypeToLabel.get(type) ?? type ?? "";
