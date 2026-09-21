import { aki } from "#common/api/client";

import { AKModal } from "#elements/dialogs/ak-modal";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Application, RACDevice, RacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-library-rac-device-launch")
export class RACLaunchDeviceLaunch extends Table<RACDevice> {
    protected override searchEnabled = true;

    public override searchPlaceholder = msg("Search for a device by name...");
    public override emptyStateMessage = msg("No devices found for this application.");
    public override rowClassNames = "pf-m-hoverable";
    public cancelable = true;

    @property({ attribute: false })
    public app: Application | null = null;

    public renderHeader(): SlottedTemplateResult {
        return html`<h1 part="form-header" class="pf-c-title pf-m-2xl">
            ${msg("Launch Device")}
        </h1>`;
    }

    protected override rowClickListener(item: RACDevice, event?: InputEvent | PointerEvent) {
        if (!item.launchUrl) {
            return super.rowClickListener(item, event);
        }

        const target = this.app?.openInNewTab ? `ak-rac-device-${item.name}` : "_self";

        window.open(item.launchUrl, target);
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<RACDevice>> {
        const devices = await aki(RacApi).racDevicesList({
            ...(await this.defaultEndpointConfig()),
            provider: this.app?.provider || 0,
        });

        if (devices.pagination.count === 1) {
            this.rowClickListener(devices.results[0]);

            if (this.parentElement instanceof AKModal) {
                this.parentElement.close();
            }
        }

        return devices;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("Protocol")],
    ];

    protected override row(item: RACDevice): SlottedTemplateResult[] {
        return [
            html`${item.name}${
                item.isPrimary
                    ? html` <span class="pf-c-badge pf-m-read">${msg("Your device")}</span>`
                    : html``
            }`,
            html`${item.protocol.toUpperCase()}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-rac-device-launch": RACLaunchDeviceLaunch;
    }
}
