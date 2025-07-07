import { EventUser, EventWithContext } from "@goauthentik/common/events";
import { truncate } from "@goauthentik/common/utils";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { msg, str } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";

/**
 * Given event with a geographical context, format it into a string for display.
 */
export function EventGeo(event: EventWithContext): SlottedTemplateResult {
    if (!event.context.geo) return nothing;

    const { city, country, continent } = event.context.geo;

    const parts = [city, country, continent].filter(Boolean);

    return html`${parts.join(", ")}`;
}

export function renderEventUser(
    event: EventWithContext,
    truncateUsername?: number,
): SlottedTemplateResult {
    if (!event.user.username) return html`-`;

    const linkOrSpan = (inner: TemplateResult, evu: EventUser) => {
        return html`${evu.pk && !evu.is_anonymous
            ? html`<a href="#/identity/users/${evu.pk}">${inner}</a>`
            : html`<span>${inner}</span>`}`;
    };

    const renderUsername = (evu: EventUser) => {
        let username = evu.username;
        if (evu.is_anonymous) {
            username = msg("Anonymous user");
        }
        if (truncateUsername) {
            return truncate(username, truncateUsername);
        }
        return username;
    };

    let body: SlottedTemplateResult = nothing;
    body = html`<div>${linkOrSpan(html`${renderUsername(event.user)}`, event.user)}</div>`;

    if (event.user.on_behalf_of) {
        return html`${body}<small>
                ${linkOrSpan(
                    html`${msg(str`On behalf of ${renderUsername(event.user.on_behalf_of)}`)}`,
                    event.user.on_behalf_of,
                )}
            </small>`;
    }
    if (event.user.authenticated_as) {
        return html`${body}<small>
                ${linkOrSpan(
                    html`${msg(
                        str`Authenticated as ${renderUsername(event.user.authenticated_as)}`,
                    )}`,
                    event.user.authenticated_as,
                )}
            </small>`;
    }

    return body;
}
