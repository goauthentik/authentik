import "@goauthentik/admin/events/EventInfo";
import { ActionToLabel } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { uiConfig } from "@goauthentik/common/ui/config";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Event, EventsApi } from "@goauthentik/api";

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
            new TableColumn(t`Action`, "action"),
            new TableColumn(t`User`, "user"),
            new TableColumn(t`Creation Date`, "created"),
            new TableColumn(t`Client IP`, "client_ip"),
            new TableColumn(t`Tenant`, "tenant_name"),
            new TableColumn(t`Actions`),
        ];
    }

    row(item: EventWithContext): TemplateResult[] {
        let geo: KeyUnknown | undefined = undefined;
        if (Object.hasOwn(item.context, "geo")) {
            geo = item.context.geo as KeyUnknown;
        }
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
                                    >${t`On behalf of ${item.user.on_behalf_of.username}`}</a
                                >
                            </small>`
                          : html``}`
                : html`-`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html`<div>${item.clientIp || t`-`}</div>
                ${geo ? html`<small>${geo.city}, ${geo.country}</small> ` : html``}`,
            html`<span>${item.tenant?.name || t`-`}</span>`,
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
