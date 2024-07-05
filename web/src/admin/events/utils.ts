import { EventWithContext } from "@goauthentik/common/events";
import { truncate } from "@goauthentik/common/utils";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";

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

export function EventUser(event: EventWithContext, truncateUsername?: number): TemplateResult {
    if (!event.user.username) {
        return html`-`;
    }
    let body = html``;
    if (event.user.is_anonymous) {
        body = html`<div>${msg("Anonymous user")}</div>`;
    } else {
        body = html`<div>
            <a href="#/identity/users/${event.user.pk}"
                >${truncateUsername
                    ? truncate(event.user?.username, truncateUsername)
                    : event.user?.username}</a
            >
        </div>`;
    }
    if (event.user.on_behalf_of) {
        body = html`${body}<small>
                <a href="#/identity/users/${event.user.on_behalf_of.pk}"
                    >${msg(str`On behalf of ${event.user.on_behalf_of.username}`)}</a
                >
            </small>`;
    }
    return body;
}
