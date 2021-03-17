import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { EventsApi, EventTopPerUser } from "authentik-api";
import PFTable from "@patternfly/patternfly/components/Table/table.css";

import "../../elements/Spinner";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-top-applications-table")
export class TopApplicationsTable extends LitElement {

    @property({attribute: false})
    topN?: EventTopPerUser[];

    static get styles(): CSSResult[] {
        return [PFTable];
    }

    firstUpdated(): void {
        new EventsApi(DEFAULT_CONFIG).eventsEventsTopPerUser({
            action: "authorize_application",
        }).then((events) => {
            this.topN = events;
        });
    }

    renderRow(event: EventTopPerUser): TemplateResult {
        return html`<tr role="row">
            <td role="cell">
                ${event.application.name}
            </td>
            <td role="cell">
                ${event.countedEvents}
            </td>
            <td role="cell">
                <progress value="${event.countedEvents}" max="${this.topN ? this.topN[0].countedEvents : 0}"></progress>
            </td>
        </tr>`;
    }

    render(): TemplateResult {
        return html`<table class="pf-c-table pf-m-compact" role="grid">
                <thead>
                    <tr role="row">
                        <th role="columnheader" scope="col">${gettext("Application")}</th>
                        <th role="columnheader" scope="col">${gettext("Logins")}</th>
                        <th role="columnheader" scope="col"></th>
                    </tr>
                </thead>
                <tbody role="rowgroup">
                    ${this.topN ? this.topN.map((e) => this.renderRow(e)) : html`<ak-spinner></ak-spinner>`}
                </tbody>
            </table>`;
    }

}
