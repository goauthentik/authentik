import { renderDefault } from "../EventInfo.shared";

import { EventWithContext } from "#common/events";

import { html } from "lit";

export const renderConfigurationEvent = (event: EventWithContext) =>
    html`<div class="pf-c-card__title">${event.context.message}</div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
