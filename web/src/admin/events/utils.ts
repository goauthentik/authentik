import { msg } from "@lit/localize";

import { EventActions } from "@goauthentik/api";

export function ActionToLabel(action?: EventActions): string {
    if (!action) return "";
    switch (action) {
        case EventActions.Login:
            return msg("Login");
        case EventActions.LoginFailed:
            return msg("Failed login");
        case EventActions.Logout:
            return msg("Logout");
        case EventActions.UserWrite:
            return msg("User was written to");
        case EventActions.SuspiciousRequest:
            return msg("Suspicious request");
        case EventActions.PasswordSet:
            return msg("Password set");
        case EventActions.SecretView:
            return msg("Secret was viewed");
        case EventActions.SecretRotate:
            return msg("Secret was rotated");
        case EventActions.InvitationUsed:
            return msg("Invitation used");
        case EventActions.AuthorizeApplication:
            return msg("Application authorized");
        case EventActions.SourceLinked:
            return msg("Source linked");
        case EventActions.ImpersonationStarted:
            return msg("Impersonation started");
        case EventActions.ImpersonationEnded:
            return msg("Impersonation ended");
        case EventActions.FlowExecution:
            return msg("Flow execution");
        case EventActions.PolicyExecution:
            return msg("Policy execution");
        case EventActions.PolicyException:
            return msg("Policy exception");
        case EventActions.PropertyMappingException:
            return msg("Property Mapping exception");
        case EventActions.SystemTaskExecution:
            return msg("System task execution");
        case EventActions.SystemTaskException:
            return msg("System task exception");
        case EventActions.SystemException:
            return msg("General system exception");
        case EventActions.ConfigurationError:
            return msg("Configuration error");
        case EventActions.ModelCreated:
            return msg("Model created");
        case EventActions.ModelUpdated:
            return msg("Model updated");
        case EventActions.ModelDeleted:
            return msg("Model deleted");
        case EventActions.EmailSent:
            return msg("Email sent");
        case EventActions.UpdateAvailable:
            return msg("Update available");
        default:
            return action;
    }
}
