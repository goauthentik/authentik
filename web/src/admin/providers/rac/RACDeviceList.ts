import "#admin/providers/rac/RACDeviceForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RACDeviceForm } from "#admin/providers/rac/RACDeviceForm";

import { EndpointsApi, RACDevice, RACProvider, RacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-rac-device-list")
export class RACDeviceListPage extends Table<RACDevice> {
    public static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    protected override searchEnabled = true;
    protected override emptyStateMessage = msg("Add a device to get started.");

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override searchPlaceholder = msg("Search for a device by name...");
    public override order = "name";

    @property({ attribute: false })
    public provider: RACProvider | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<RACDevice>> {
        return aki(RacApi).racDevicesList({
            ...(await this.defaultEndpointConfig()),
            provider: this.provider?.pk ?? 0,
            superuserFullList: true,
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Protocol")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Device(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: RACDevice) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: RACDevice) => {
                return aki(EndpointsApi).endpointsDevicesUsedByList({
                    deviceUuid: item.deviceUuid!,
                });
            }}
            .delete=${(item: RACDevice) => {
                return aki(EndpointsApi).endpointsDevicesDestroy({
                    deviceUuid: item.deviceUuid!,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: RACDevice): SlottedTemplateResult[] {
        return [
            html`<a href="#/endpoints/devices/${item.deviceUuid}">${item.name}</a>`,
            html`${item.protocols.map((entry) => entry.protocol.toUpperCase()).join(", ")}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(RACDeviceForm, item.overridePk ?? null, item.name, {
                    modalProps: {
                        provider: this.provider,
                        // Devices which are enrolled through a connector have no
                        // override until one is created for them
                        device: item.overridePk ? null : item.deviceUuid,
                    },
                })}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(RACDeviceForm, {
            provider: this.provider,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-device-list": RACDeviceListPage;
    }
}
