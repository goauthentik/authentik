import "#elements/Spinner";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { EventsApi, EventTopPerUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFTable from "@patternfly/patternfly/components/Table/table.css";

@customElement("ak-top-applications-table")
export class TopApplicationsTable extends AKElement {
    @property({ attribute: false })
    topN?: EventTopPerUser[];

    static styles: CSSResult[] = [PFTable];

    firstUpdated(): void {
        new EventsApi(DEFAULT_CONFIG)
            .eventsEventsTopPerUserList({
                action: "authorize_application",
                topN: 11,
            })
            .then((events) => {
                this.topN = events;
            });
    }

    renderRow(event: EventTopPerUser): TemplateResult {
        return html`<tr>
            <td>${event.application.name}</td>
            <td>${event.countedEvents}</td>
            <td>
                <progress
                    value="${event.countedEvents}"
                    max="${this.topN ? this.topN[0].countedEvents : 0}"
                ></progress>
            </td>
        </tr>`;
    }

    render(): TemplateResult {
        return html`<table class="pf-c-table pf-m-compact">
            <thead>
                <tr>
                    <th scope="col">${msg("Application")}</th>
                    <th scope="col">${msg("Logins")}</th>
                    <th scope="col"></th>
                </tr>
            </thead>
            <tbody role="rowgroup">
                ${this.topN
                    ? this.topN.map((e) => this.renderRow(e))
                    : html`<ak-spinner></ak-spinner>`}
            </tbody>
        </table>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-top-applications-table": TopApplicationsTable;
    }
}
