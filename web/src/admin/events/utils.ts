import { EventWithContext } from "@goauthentik/common/events";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

import { EventActions, SeverityEnum } from "@goauthentik/api";

export function EventGeo(event: EventWithContext): TemplateResult {
    let geo: KeyUnknown | undefined = undefined;
    if (Object.hasOwn(event.context, "geo")) {
        geo = event.context.geo as KeyUnknown;
        const parts = [geo.city, geo.country, geo.continent].filter(
            (v) => v !== "" && v !== undefined,
        );
        return html`${parts.join(", ")}`;
    }
    return html``;
}

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

export function SeverityToLabel(severity: SeverityEnum | null | undefined): string {
    if (!severity) return msg("Unknown severity");
    switch (severity) {
        case SeverityEnum.Alert:
            return msg("Alert");
        case SeverityEnum.Notice:
            return msg("Notice");
        case SeverityEnum.Warning:
            return msg("Warning");
    }
    return msg("Unknown severity");
}
