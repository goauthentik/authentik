import "#admin/events/EventMap";
import "#admin/events/EventVolumeChart";
import "#admin/reports/ExportButton";
import "#components/ak-event-info";
import "#elements/Tabs";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";

import { WithLicenseSummary } from "#elements/mixins/license";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { EventGeo, renderEventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-event-list")
export class EventListPage extends WithLicenseSummary(TablePage<Event>) {
    expandable = true;
    supportsQL = true;

    public pageTitle = msg("Event Log");
    public pageDescription = "";

    public pageIcon = "pf-icon pf-icon-catalog";
    protected override searchEnabled = true;

    @property()
    order = "-created";

    static styles: CSSResult[] = [
        ...TablePage.styles,
        PFGrid,
        css`
            .pf-m-no-padding-bottom {
                padding-bottom: 0;
            }
        `,
    ];

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Action"), "action"],
        [msg("User"), "user"],
        [msg("Creation Date"), "created"],
        [msg("Client IP"), "client_ip"],
        [msg("Brand"), "brand_name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override rowLabel(item: Event): string | null {
        return actionToLabel(item.action);
    }

    renderSectionBefore(): TemplateResult {
        if (this.hasEnterpriseLicense) {
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
                        this.search = `event_uuid = "${ev.detail.eventId}"`;
                        this.page = 1;
                        this.fetch();
                    }}
                ></ak-events-map>
            </div>`;
        }
        return html`<div class="pf-c-page__main-section pf-m-no-padding-bottom">
            <ak-events-volume-chart
                .query=${{
                    page: this.page,
                    search: this.search,
                }}
            ></ak-events-volume-chart>
        </div>`;
    }

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`<div>${actionToLabel(item.action)}</div>
                <small>${item.app}</small>`,
            renderEventUser(item),
            Timestamp(item.created),
            html`<div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
            html`<span>${item.brand?.name || msg("-")}</span>`,
            html`<a href="#/events/log/${item.pk}">
                <pf-tooltip position="top" content=${msg("Show details")}>
                    <i class="fas fa-share-square" aria-hidden="true"></i>
                </pf-tooltip>
            </a>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html`<ak-event-info .event=${item as EventWithContext}></ak-event-info>`;
    }

    protected renderToolbar(): TemplateResult {
        return html`${super.renderToolbar()}
            <ak-reports-export-button
                .createExport=${async () => {
                    await this.createExport();
                }}
            ></ak-reports-export-button>`;
    }

    private async createExport() {
        await new EventsApi(DEFAULT_CONFIG).eventsEventsExportCreate({
            ...(await this.defaultEndpointConfig()),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-list": EventListPage;
    }
}
