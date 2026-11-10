import { EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export const renderSystemTaskException = (event: EventWithContext) =>
    html`<div class="pf-l-flex">
        <div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("Exception")}</div>
            <div class="pf-c-card__body">
                <pre>${event.context.message}</pre>
            </div>
        </div>
    </div>`;
