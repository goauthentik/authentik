import "#elements/Tabs";
import { WithLicenseSummary } from "#elements/mixins/license";
import { updateURLParams } from "#elements/router/RouteMatch";
import "@goauthentik/admin/events/EventMap";
import "@goauthentik/admin/events/EventVolumeChart";
import { EventGeo, EventUser } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { actionToLabel } from "@goauthentik/common/labels";
import { formatElapsedTime } from "@goauthentik/common/temporal";
import "@goauthentik/components/ak-event-info";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import { SlottedTemplateResult } from "@goauthentik/elements/types";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { Event, EventsApi, LicenseSummaryStatusEnum } from "@goauthentik/api";

@customElement("ak-event-list")
export class EventListPage extends WithLicenseSummary(TablePage<Event>) {
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
        // @ts-expect-error
        return super.styles.concat(
            PFGrid,
            css`
                .pf-m-no-padding-bottom {
                    padding-bottom: 0;
                }
            `,
        );
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
        if (this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed) {
            return html`<div
                class="pf-l-grid pf-m-gutter pf-c-page__main-section pf-m-no-padding-bottom"
            >
                <ak-events-volume-chart
                    class="pf-l-grid__item pf-m-12-col pf-m-4-col-on-xl pf-m-4-col-on-2xl "
                    .query=${{
                        page: this.page,
                        search: this.search,
                    }}
                    with-map
                ></ak-events-volume-chart>
                <ak-events-map
                    class="pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl pf-m-8-col-on-2xl "
                    .events=${this.data}
                    @select-event=${(ev: CustomEvent<{ eventId: string }>) => {
                        this.search = ev.detail.eventId;
                        this.page = 1;
                        updateURLParams({
                            search: this.search,
                            tablePage: this.page,
                        });
                        this.fetch();
                    }}
                ></ak-events-map>
            </div>`;
        }
        return html`<ak-events-volume-chart
            .query=${{
                page: this.page,
                search: this.search,
            }}
        ></ak-events-volume-chart>`;
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
