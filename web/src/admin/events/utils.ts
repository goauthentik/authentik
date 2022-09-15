import { t } from "@lingui/macro";

import { EventActions } from "@goauthentik/api";

export function ActionToLabel(action?: EventActions): string {
    if (!action) return "";
    switch (action) {
        case EventActions.Login:
            return t`Login`;
        case EventActions.LoginFailed:
            return t`Failed login`;
        case EventActions.Logout:
            return t`Logout`;
        case EventActions.UserWrite:
            return t`User was written to`;
        case EventActions.SuspiciousRequest:
            return t`Suspicious request`;
        case EventActions.PasswordSet:
            return t`Password set`;
        case EventActions.SecretView:
            return t`Secret was viewed`;
        case EventActions.SecretRotate:
            return t`Secret was rotated`;
        case EventActions.InvitationUsed:
            return t`Invitation used`;
        case EventActions.AuthorizeApplication:
            return t`Application authorized`;
        case EventActions.SourceLinked:
            return t`Source linked`;
        case EventActions.ImpersonationStarted:
            return t`Impersonation started`;
        case EventActions.ImpersonationEnded:
            return t`Impersonation ended`;
        case EventActions.FlowExecution:
            return t`Flow execution`;
        case EventActions.PolicyExecution:
            return t`Policy execution`;
        case EventActions.PolicyException:
            return t`Policy exception`;
        case EventActions.PropertyMappingException:
            return t`Property Mapping exception`;
        case EventActions.SystemTaskExecution:
            return t`System task execution`;
        case EventActions.SystemTaskException:
            return t`System task exception`;
        case EventActions.SystemException:
            return t`General system exception`;
        case EventActions.ConfigurationError:
            return t`Configuration error`;
        case EventActions.ModelCreated:
            return t`Model created`;
        case EventActions.ModelUpdated:
            return t`Model updated`;
        case EventActions.ModelDeleted:
            return t`Model deleted`;
        case EventActions.EmailSent:
            return t`Email sent`;
        case EventActions.UpdateAvailable:
            return t`Update available`;
        default:
            return action;
    }
}
