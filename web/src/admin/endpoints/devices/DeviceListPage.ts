import "#elements/cards/AggregateCard";
import "#elements/forms/DeleteBulkForm";
import "#admin/endpoints/devices/DeviceForm";
import "#admin/endpoints/devices/DeviceAddHowTo";
import "#elements/forms/ModalForm";

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
    public pageTitle = msg("Devices");
    public pageDescription = "";
    public pageIcon = "fa fa-laptop";

    checkbox = true;

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
        [msg("Actions"), null, msg("Row Actions")],
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
                ${msg("Endpoint Devices are in preview.")}
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
        return [
            html`<a href="#/endpoints/devices/${item.deviceUuid}">
                <div>${item.facts.data.network?.hostname || item.name}</div>
            </a>`,
            html`${osFamilyToLabel(item.facts.data.os?.family)} ${item.facts.data.os?.version}`,
            html`${item.group || "-"}`,
            item.facts.created ? Timestamp(item.facts.created) : html`-`,
            html`<ak-forms-modal>
                <span slot="submit">${msg("Update")}</span>
                <span slot="header">${msg("Update Device")}</span>
                <ak-endpoints-device-form slot="form" .instancePk=${item.deviceUuid}>
                </ak-endpoints-device-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate() {
        return html`<ak-endpoints-device-add>
            <button slot="trigger" class="pf-c-button pf-m-secondary">${msg("Add")}</button>
        </ak-endpoints-device-add>`;
    }

    renderToolbarSelected() {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Endpoint Device(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: EndpointDevice) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: EndpointDevice) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesUsedByList({
                    deviceUuid: item.deviceUuid!,
                });
            }}
            .delete=${(item: EndpointDevice) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesDestroy({
                    deviceUuid: item.deviceUuid!,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-list": DeviceListPage;
    }
}
