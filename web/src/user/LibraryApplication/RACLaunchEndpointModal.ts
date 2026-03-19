import { DEFAULT_CONFIG } from "#common/api/config";

import { AKModal } from "#elements/modals/ak-modal";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Application, Endpoint, RacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-library-rac-endpoint-launch")
export class RACLaunchEndpointLaunch extends Table<Endpoint> {
    public override clickable = true;
    protected override searchEnabled = true;

    protected override rowClickListener(item: Endpoint, event?: InputEvent | PointerEvent) {
        if (!item.launchUrl) {
            return super.rowClickListener(item, event);
        }

        const target = this.app?.openInNewTab ? `ak-rac-endpoint-${item.name}` : "_self";

        window.open(item.launchUrl, target);
    }

    @property({ attribute: false })
    public app?: Application;

    async apiEndpoint(): Promise<PaginatedResponse<Endpoint>> {
        const endpoints = await new RacApi(DEFAULT_CONFIG).racEndpointsList({
            ...(await this.defaultEndpointConfig()),
            provider: this.app?.provider || 0,
        });

        if (endpoints.pagination.count === 1) {
            this.rowClickListener(endpoints.results[0]);

            if (this.parentElement instanceof AKModal) {
                this.parentElement.close();
            }
        }
        return endpoints;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
    ];

    row(item: Endpoint): SlottedTemplateResult[] {
        return [html`${item.name}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-rac-endpoint-launch": RACLaunchEndpointLaunch;
    }
}
