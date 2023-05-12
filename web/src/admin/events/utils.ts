import { EventWithContext } from "@goauthentik/common/events";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { t } from "@lingui/macro";

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

export function SeverityToLabel(severity: SeverityEnum | null | undefined): string {
    if (!severity) return t`Unknown severity`;
    switch (severity) {
        case SeverityEnum.Alert:
            return t`Alert`;
        case SeverityEnum.Notice:
            return t`Notice`;
        case SeverityEnum.Warning:
            return t`Warning`;
    }
    return t`Unknown severity`;
}
