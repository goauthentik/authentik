import { EventWithContext } from "@goauthentik/common/events";
import { truncate } from "@goauthentik/common/utils";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";

/**
 * Given event with a geographical context, format it into a string for display.
 */
export function EventGeo(event: EventWithContext): SlottedTemplateResult {
    if (!event.context.geo) return nothing;

    const { city, country, continent } = event.context.geo;

    const parts = [city, country, continent].filter(Boolean);

    return html`${parts.join(", ")}`;
}

export function EventUser(
    event: EventWithContext,
    truncateUsername?: number,
): SlottedTemplateResult {
    if (!event.user.username) return html`-`;

    let body: SlottedTemplateResult = nothing;

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
        return html`${body}<small>
                <a href="#/identity/users/${event.user.on_behalf_of.pk}"
                    >${msg(str`On behalf of ${event.user.on_behalf_of.username}`)}</a
                >
            </small>`;
    }

    return body;
}
