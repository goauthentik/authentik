import "#elements/cards/AggregateCard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse } from "#elements/table/Table";
import { TableColumn } from "#elements/table/TableColumn";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { EndpointDevice, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-endpoints-device-list")
export class DeviceListPage extends TablePage<EndpointDevice> {
    pageTitle(): string {
        return msg("Devices");
    }
    pageDescription(): string | undefined {
        return undefined;
    }
    pageIcon(): string {
        return "fa fa-laptop";
    }

    static styles: CSSResult[] = [...super.styles, PFGrid];

    async apiEndpoint(): Promise<PaginatedResponse<EndpointDevice>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesList(
            await this.defaultEndpointConfig(),
        );
    }
    columns(): TableColumn[] {
        return [new TableColumn("Name"), new TableColumn("OS")];
    }

    renderSectionBefore() {
        return html`
            <section class="pf-c-page__main-section pf-m-no-padding-bottom">
                <div
                    class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
                >
                    <ak-aggregate-card
                        class="pf-l-grid__item"
                        icon="fa fa-laptop"
                        header=${msg("Devices")}
                    >
                        ${this.data?.pagination.count}
                    </ak-aggregate-card>
                </div>
            </section>
        `;
    }

    row(item: EndpointDevice): SlottedTemplateResult[] {
        return [
            html`${item.data.network.hostname}`,
            html`${item.data.os.family} ${item.data.os.version}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-list": DeviceListPage;
    }
}
