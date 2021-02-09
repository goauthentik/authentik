import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Event } from "../../api/Events";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import { time } from "../../utils";
import "./EventInfo";

@customElement("ak-event-list")
export class EventListPage extends TablePage<Event> {
    expandable = true;

    pageTitle(): string {
        return "Event Log";
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-catalog";
    }
    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "-created";

    apiEndpoint(page: number): Promise<AKResponse<Event>> {
        return Event.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Action", "action"),
            new TableColumn("User", "user"),
            new TableColumn("Creation Date", "created"),
            new TableColumn("Client IP", "client_ip"),
        ];
    }
    row(item: Event): TemplateResult[] {
        return [
            html`<div>${item.action}</div>
            <small>${item.app}</small>`,
            html`<div>${item.user.username}</div>
            ${item.user.on_behalf_of ? html`<small>
                ${gettext(`On behalf of ${item.user.on_behalf_of.username}`)}
            </small>` : html``}`,
            html`<span>${time(item.created).toLocaleString()}</span>`,
            html`<span>${item.client_ip}</span>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html`
        <td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <ak-event-info .event=${item}></ak-event-info>
            </div>
        </td>
        <td></td>
        <td></td>
        <td></td>`;
    }

}
