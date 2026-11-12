import { renderDefault } from "../EventInfo.shared";

import { EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export const renderPropertyMappingException = (event: EventWithContext) =>
    html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Exception")}</div>
                <div class="pf-c-card__body">
                    <pre>${event.context.message || event.context.error}</pre>
                </div>
            </div>
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Expression")}</div>
                <div class="pf-c-card__body">
                    <code>${event.context.expression}</code>
                </div>
            </div>
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
