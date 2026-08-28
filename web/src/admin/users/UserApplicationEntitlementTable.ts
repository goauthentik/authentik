import { aki } from "#common/api/client";

import { paramURL } from "#elements/router/RouterOutlet";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { ApplicationEntitlement, CoreApi, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-application-entitlement-table")
export class UserApplicationEntitlementTable extends Table<ApplicationEntitlement> {
    @property({ attribute: false })
    user?: User;

    protected override searchEnabled = true;

    public override order = "app__name";

    async apiEndpoint(): Promise<PaginatedResponse<ApplicationEntitlement>> {
        return aki(CoreApi).coreApplicationEntitlementsList({
            ...(await this.defaultEndpointConfig()),
            forUser: this.user?.pk,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Application"), "app__name"],
        [msg("Name"), "name"],
    ];

    row(item: ApplicationEntitlement): SlottedTemplateResult[] {
        return [
            html`<a
                href=${paramURL(`/core/applications/${item.appSlug}`, {
                    page: "page-app-entitlements",
                })}
            >
                ${item.appName}
            </a>`,
            html`${item.name}`,
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module">
                <span>
                    ${msg("No application entitlements.", {
                        id: "user.entitlements.empty.label",
                    })}
                </span>
                <div slot="body">
                    ${msg("This user has not been granted any application entitlements.", {
                        id: "user.entitlements.empty.description",
                    })}
                </div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-application-entitlement-table": UserApplicationEntitlementTable;
    }
}
