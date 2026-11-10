import { renderDefault } from "../EventInfo.shared";

import { EventWithContext } from "#common/events";

import { msg, str } from "@lit/localize";
import { html } from "lit";

export const renderLoginFailed = (event: EventWithContext) =>
    html` <div class="pf-c-card__title">
            ${msg(str`Attempted to log in as ${event.context.username}`)}
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
