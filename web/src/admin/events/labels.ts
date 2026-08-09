import { MessageFormatter } from "#common/ui/locale/format";

import { EventActions } from "@goauthentik/api";

import { msg } from "@lit/localize";

const EventActionLabelRecord: { [key in EventActions]?: MessageFormatter<string> } = {
    [EventActions.Login]: () => msg("Login", { id: "events.map.kind.login.label" }),
    [EventActions.LoginFailed]: () =>
        msg("Failed login", {
            id: "events.map.kind.login-failed.label",
        }),
    [EventActions.Logout]: () => msg("Logout", { id: "events.map.kind.logout.label" }),
    [EventActions.AuthorizeApplication]: () =>
        msg("Authorize Application", {
            id: "events.map.kind.authorize-application.label",
        }),
    [EventActions.UnknownDefaultOpenApi]: () => msg("Other", { id: "events.map.kind.other.label" }),
};

export function formatEventAction(action?: string): string {
    const formatter = EventActionLabelRecord[action as EventActions];

    // Anything unmapped (or missing) reads as the catch-all bucket.
    return formatter?.() || EventActionLabelRecord[EventActions.UnknownDefaultOpenApi]!();
}
