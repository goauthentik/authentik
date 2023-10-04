import "@goauthentik/admin/roles/RolePermissionForm";
import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { groupBy } from "@goauthentik/app/common/utils";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, Permission } from "@goauthentik/api";

@customElement("ak-role-permissions-table")
export class RolePermissionTable extends Table<Permission> {
    @property()
    roleUuid?: string;

    searchEnabled(): boolean {
        return true;
    }

    apiEndpoint(page: number): Promise<PaginatedResponse<Permission>> {
        return new CoreApi(DEFAULT_CONFIG).coreRbacPermissionsList({
            role: this.roleUuid,
            page: page,
            search: this.search,
        });
    }

    groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn("Permission", ""), new TableColumn("")];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Assign")} </span>
                <span slot="header"> ${msg("Assign permission to role")} </span>
                <ak-role-permission-form roleUuid=${ifDefined(this.roleUuid)} slot="form">
                </ak-role-permission-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Assign permission")}
                </button>
            </ak-forms-modal>
        `;
    }

    row(item: Permission): TemplateResult[] {
        return [html`${item.name}`, html`✓`];
    }
}
