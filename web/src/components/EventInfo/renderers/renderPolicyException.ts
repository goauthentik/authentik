import { getModelInfo, renderDefault } from "../EventInfo.shared";

import { EventContext, EventModel, EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

// Broken out and exported because the exact same block was duplicated in renderPolicyExecution.
//
export const renderPolicyRequest = (context: EventContext) =>
    html`<div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("Binding")}</div>
            ${getModelInfo(context.binding as EventModel)}
        </div>
        <div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("Request")}</div>
            <div class="pf-c-card__body">
                <ul class="pf-c-list">
                    <li>
                        ${msg("Object")}:
                        ${getModelInfo((context.request as EventContext).obj as EventModel)}
                    </li>
                    <li>
                        <span
                            >${msg("Context")}:
                            <code
                                >${JSON.stringify(
                                    (context.request as EventContext).context,
                                    null,
                                    4,
                                )}</code
                            ></span
                        >
                    </li>
                </ul>
            </div>
        </div>`;

export function renderPolicyException(event: EventWithContext) {
    return html`<div class="pf-l-flex">
            ${renderPolicyRequest(event.context as EventContext)}
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Exception")}</div>
                <div class="pf-c-card__body">
                    <code>${event.context.message || event.context.error}</code>
                </div>
            </div>
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
}
