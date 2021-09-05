import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { Event, EventsApi } from "@goauthentik/api";
import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EventWithContext } from "../../api/Events";
import { PAGE_SIZE } from "../../constants";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import "./EventInfo";
import { ActionToLabel } from "./utils";

@customElement("ak-event-list")
export class EventListPage extends TablePage<Event> {
    expandable = true;

    pageTitle(): string {
        return t`Event Log`;
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
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Action`, "action"),
            new TableColumn(t`User`, "user"),
            new TableColumn(t`Creation Date`, "created"),
            new TableColumn(t`Client IP`, "client_ip"),
            new TableColumn(t`Tenant`, "tenant_name"),
            new TableColumn(t`Actions`),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`<div>${ActionToLabel(item.action)}</div>
                <small>${item.app}</small>`,
            item.user?.username
                ? html`<a href="#/identity/users/${item.user.pk}"> ${item.user?.username} </a>
                      ${item.user.on_behalf_of
                          ? html`<small>
                                ${t`On behalf of ${item.user.on_behalf_of.username}`}
                            </small>`
                          : html``}`
                : html`-`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<span>${item.clientIp || "-"}</span>`,
            html`<span>${item.tenant?.name || "-"}</span>`,
            html`<a href="#/events/log/${item.pk}">
                <i class="fas fas fa-share-square"></i>
            </a>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <ak-event-info .event=${item as EventWithContext}></ak-event-info>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }
}
