import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { Event, EventsApi } from "../../api";
import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EventWithContext } from "../../api/Events";
import { PAGE_SIZE } from "../../constants";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
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
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE * 3,
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
    row(item: EventWithContext): TemplateResult[] {
        return [
            html`<div>${item.action}</div>
            <small>${item.app}</small>`,
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

}
