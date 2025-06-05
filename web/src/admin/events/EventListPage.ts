import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-event-info";
import "#admin/events/EventVolumeChart";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { EventGeo, EventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

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

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList(await this.defaultEndpointConfig());
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

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`<div>${actionToLabel(item.action)}</div>
                <small>${item.app}</small>`,
            EventUser(item),
            html`<div>${formatElapsedTime(item.created)}</div>
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
        return html` <td role="cell" colspan="5">
                <div class="pf-c-table__expandable-row-content">
                    <ak-event-info .event=${item as EventWithContext}></ak-event-info>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-list": EventListPage;
    }
}
