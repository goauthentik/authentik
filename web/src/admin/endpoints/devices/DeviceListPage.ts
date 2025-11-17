import "#elements/cards/AggregateCard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { osFamilyToLabel } from "#admin/endpoints/devices/utils";

import { EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-endpoints-device-list")
export class DeviceListPage extends TablePage<EndpointDevice> {
    public pageTitle = msg("Device");
    public pageDescription = "";
    public pageIcon = "fa fa-laptop";

    static styles: CSSResult[] = [
        ...super.styles,
        PFGrid,
        PFBanner,
        css`
            .pf-m-no-padding-bottom {
                padding-bottom: 0;
            }
        `,
    ];

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("OS")],
        [msg("Group")],
        [msg("Last updated")],
    ];

    ordering = "name";

    async apiEndpoint(): Promise<PaginatedResponse<EndpointDevice>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesList(
            await this.defaultEndpointConfig(),
        );
    }

    renderSectionBefore() {
        return html`
            <div class="pf-c-banner pf-m-info">
                ${msg("Endpoints are in preview.")}
                <a href="mailto:hello+feature/platform@goauthentik.io"
                    >${msg("Send us feedback!")}</a
                >
            </div>
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
                >
                    <ak-aggregate-card
                        role="status"
                        class="pf-l-grid__item"
                        icon="fa fa-laptop"
                        label=${msg("Total devices")}
                        subtext=${msg("Total count of devices across all groups")}
                    >
                        ${this.data?.pagination.count}
                    </ak-aggregate-card>
                </div>
            </section>
        `;
    }

    row(item: EndpointDevice): SlottedTemplateResult[] {
        const lastUpdated = item.connectionsObj.map((c) => c.latestSnapshot?.created).sort();
        return [
            html`<a href="#/endpoints/devices/${item.deviceUuid}">
                <div>${item.facts.network?.hostname || item.name}</div>
            </a>`,
            html`${osFamilyToLabel(item.facts.os?.family)} ${item.facts.os?.version}`,
            html`${item.group || "-"}`,
            lastUpdated.length > 0 ? Timestamp(lastUpdated[0]) : html`-`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-list": DeviceListPage;
    }
}
