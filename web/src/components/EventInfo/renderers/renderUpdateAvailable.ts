import { EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderUpdateAvailable(event: EventWithContext) {
    let url = `https://github.com/goauthentik/authentik/releases/tag/version%2F${event.context.new_version}`;

    if (event.context.changelog) {
        url = event.context.changelog as string;
    }

    return html`<div class="pf-c-card__title">${msg("New version available")}</div>
        <div class="pf-c-card__body">
            <a target="_blank" href=${url}> ${event.context.new_version} </a>
        </div>`;
}
