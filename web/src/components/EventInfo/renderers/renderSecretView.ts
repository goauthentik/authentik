import { getModelInfo } from "../EventInfo.shared";

import { EventModel, EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderSecretView(event: EventWithContext) {
    return html` <div class="pf-c-card__title">${msg("Secret:")}</div>
        ${getModelInfo(event.context.secret as EventModel)}`;
}
