import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";
import { Event, EventsApi } from "authentik-api";

import "../forms/DeleteForm";
import "../Tabs";
import "../buttons/ModalButton";
import "../buttons/SpinnerButton";
import "../buttons/Dropdown";
import "../../pages/events/EventInfo";
import { PAGE_SIZE } from "../../constants";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EventWithContext } from "../../api/Events";

@customElement("ak-object-changelog")
export class ObjectChangelog extends Table<Event> {
    expandable = true;

    @property()
    order = "-created";

    @property()
    targetModelPk!: string | number;

    @property()
    targetModelApp!: string;

    @property()
    targetModelName!: string;

    apiEndpoint(page: number): Promise<AKResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            action: "model_",
            page: page,
            ordering: this.order,
            pageSize: PAGE_SIZE,
            contextModelApp: this.targetModelApp,
            contextModelName: this.targetModelName,
            contextModelPk: this.targetModelPk.toString(),
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Action", "action"),
            new TableColumn("User", "enabled"),
            new TableColumn("Creation Date", "created"),
            new TableColumn("Client IP", "client_ip"),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`${item.action}`,
            html`<div>${item.user?.username}</div>
            ${item.user.on_behalf_of ? html`<small>
                ${gettext(`On behalf of ${item.user.on_behalf_of.username}`)}
            </small>` : html``}`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<span>${item.clientIp}</span>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html`
        <td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <ak-event-info .event=${item as EventWithContext}></ak-event-info>
            </div>
        </td>
        <td></td>
        <td></td>
        <td></td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state header=${gettext("No Events found.")} icon="pf-icon-module">
            <div slot="body">
                ${gettext("No matching events could be found.")}
            </div>
        </ak-empty-state>`);
    }

}
