import { getEmailInfo } from "../EventInfo.shared";

import { EventWithContext } from "#common/events";
import { staticURL } from "#common/urls";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderEmailSent(event: EventWithContext) {
    let body = event.context.body as string;
    body = body.replace("cid:logo", staticURL("/static/dist/assets/icons/icon_left_brand.png"));

    return html`<div class="pf-c-card__title">${msg("Email info:")}</div>
        <div class="pf-c-card__body">${getEmailInfo(event.context)}</div>
        <ak-expand>
            <iframe srcdoc=${body}></iframe>
        </ak-expand>`;
}
