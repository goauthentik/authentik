import { getModelInfo, renderDefault } from "../EventInfo.shared";

import { EventModel, EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

export const renderLogin = (event: EventWithContext) =>
    "using_source" in event.context
        ? html`<div class="pf-l-flex">
              <div class="pf-l-flex__item">
                  <div class="pf-c-card__title">${msg("Using source")}</div>
                  ${getModelInfo(event.context.using_source as EventModel)}
              </div>
          </div>`
        : renderDefault(event);
