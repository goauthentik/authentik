import "@goauthentik/admin/events/EventVolumeChart";
import { EventGeo, EventUser } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { actionToLabel } from "@goauthentik/common/labels";
import { uiConfig } from "@goauthentik/common/ui/config";
import { getRelativeTime } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-event-info";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
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

    static get styles(): CSSResult[] {
        return super.styles.concat(css`
            .pf-m-no-padding-bottom {
                padding-bottom: 0;
            }
        `);
    }

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
            new TableColumn(msg("Brand"), "brand_name"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderSectionBefore(): TemplateResult {
        return html`
            <div class="pf-c-page__main-section pf-m-no-padding-bottom">
                <ak-events-volume-chart
                    .query=${{
                        page: this.page,
                        search: this.search,
                    }}
                ></ak-events-volume-chart>
            </div>
        `;
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`<div>${actionToLabel(item.action)}</div>
                <small>${item.app}</small>`,
            EventUser(item),
            html`<div>${getRelativeTime(item.created)}</div>
                <small>${item.created.toLocaleString()}</small>`,
            html`<div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
            html`<span>${item.brand?.name || msg("-")}</span>`,
            html`<a href="#/events/log/${item.pk}">
                <pf-tooltip position="top" content=${msg("Show details")}>
                    <i class="fas fa-share-square"></i>
                </pf-tooltip>
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
