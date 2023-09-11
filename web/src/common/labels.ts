import { msg } from "@lit/localize";

import { EventActions, IntentEnum, SeverityEnum } from "@goauthentik/api";

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
