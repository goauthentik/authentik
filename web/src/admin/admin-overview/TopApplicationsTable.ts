import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Spinner";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFTable from "@patternfly/patternfly/components/Table/table.css";

import { EventTopPerUser, EventsApi } from "@goauthentik/api";

@customElement("ak-top-applications-table")
export class TopApplicationsTable extends AKElement {
    @property({ attribute: false })
    topN?: EventTopPerUser[];

    static get styles(): CSSResult[] {
        return [PFTable];
    }

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
        return html`<tr role="row">
            <td role="cell">${event.application.name}</td>
            <td role="cell">${event.countedEvents}</td>
            <td role="cell">
                <progress
                    value="${event.countedEvents}"
                    max="${this.topN ? this.topN[0].countedEvents : 0}"
                ></progress>
            </td>
        </tr>`;
    }

    render(): TemplateResult {
        return html`<table class="pf-c-table pf-m-compact" role="grid">
            <thead>
                <tr role="row">
                    <th role="columnheader" scope="col">${msg("Application")}</th>
                    <th role="columnheader" scope="col">${msg("Logins")}</th>
                    <th role="columnheader" scope="col"></th>
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
