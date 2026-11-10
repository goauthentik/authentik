import { renderDefault } from "../EventInfo.shared";

import { EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export const renderLogout = (event: EventWithContext) =>
    Object.keys(event.context).length > 0
        ? renderDefault(event)
        : html`<span>${msg("No additional data available.")}</span>`;
