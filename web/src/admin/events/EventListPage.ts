import "@goauthentik/admin/events/EventInfo";
import { ActionToLabel, EventGeo } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Event, EventsApi } from "@goauthentik/api";

@customElement("ak-event-list")
export class EventListPage extends TablePage<Event> {
    expandable = true;

    pageTitle(): string {
        return msg("Event Log");
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

    async apiEndpoint(page: number): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Action"), "action"),
            new TableColumn(msg("User"), "user"),
            new TableColumn(msg("Creation Date"), "created"),
            new TableColumn(msg("Client IP"), "client_ip"),
            new TableColumn(msg("Tenant"), "tenant_name"),
            new TableColumn(msg("Actions")),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`<div>${ActionToLabel(item.action)}</div>
                <small>${item.app}</small>`,
            item.user?.username
                ? html`<div>
                          <a href="#/identity/users/${item.user.pk}">${item.user?.username}</a>
                      </div>
                      ${item.user.on_behalf_of
                          ? html`<small>
                                <a href="#/identity/users/${item.user.on_behalf_of.pk}"
                                    >${msg(str`On behalf of ${item.user.on_behalf_of.username}`)}</a
                                >
                            </small>`
                          : html``}`
                : html`-`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<div>${item.clientIp || msg("-")}</div>

                <small>${EventGeo(item)}</small>`,
            html`<span>${item.tenant?.name || msg("-")}</span>`,
            html`<a href="#/events/log/${item.pk}">
                <i class="fas fa-share-square"></i>
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
