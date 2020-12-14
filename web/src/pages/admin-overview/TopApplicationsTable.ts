import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Event, TopNEvents } from "../../api/events";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/Spinner";

@customElement("ak-top-applications-table")
export class TopApplicationsTable extends LitElement {

    @property({attribute: false})
    topN?: TopNEvents[];

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    firstUpdated(): void {
        Event.topForUser("authorize_application").then(events => this.topN = events);
    }

    renderRow(event: TopNEvents): TemplateResult {
        return html`<tr role="row">
            <td role="cell">
                ${event.application.name}
            </td>
            <td role="cell">
                ${event.counted_events}
            </td>
            <td role="cell">
                <progress value="${event.counted_events}" max="${this.topN ? this.topN[0].counted_events : 0}"></progress>
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
