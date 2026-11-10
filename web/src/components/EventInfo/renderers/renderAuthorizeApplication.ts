import { getModelInfo, renderDefault } from "../EventInfo.shared";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { EventModel, EventWithContext } from "#common/events";

import { toAdminInterface } from "#elements/router/core/interfaces";

import { FlowsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { until } from "lit/directives/until.js";

export const renderAuthorizeApplication = (event: EventWithContext) =>
    html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Authorized application:")}</div>
                <div class="pf-c-card__body">
                    ${getModelInfo(event.context.authorized_application as EventModel)}
                </div>
            </div>
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Using flow")}</div>
                <div class="pf-c-card__body">
                    <span
                        >${until(
                            aki(FlowsApi)
                                .flowsInstancesList({
                                    flowUuid: event.context.flow as string,
                                })
                                .then((resp) => {
                                    return html`<a
                                        href=${toAdminInterface(
                                            `flow/flows/${resp.results[0].slug}`,
                                        )}
                                        >${resp.results[0].name}</a
                                    >`;
                                }),
                            html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`,
                        )}
                    </span>
                </div>
            </div>
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
