import { EventUser, EventWithContext } from "#common/events";
import { truncate } from "#common/strings";

import { SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";

export function formatUUID(hex: string): string {
    if (hex.length < 32) {
        return hex;
    }
    return `${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20, 32)}`;
}

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
    if (event.context.device) {
        return html`${body}<small>
                <a href="#/endpoints/devices/${formatUUID(event.context.device.pk)}">
                    ${msg(str`Via ${event.context.device.name}`)}
                </a>
            </small>`;
    }

    return body;
}
