import "@goauthentik/admin/tenants/TenantForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/ObjectPermissionModal";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, RbacPermissionsAssignedByUsersListModelEnum, Tenant } from "@goauthentik/api";

@customElement("ak-tenant-list")
export class TenantListPage extends TablePage<Tenant> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Tenants");
    }
    pageDescription(): string {
        return msg("Configure visual settings and defaults for different domains.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-tenant";
    }

    checkbox = true;

    @property()
    order = "domain";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Tenant>> {
        return new CoreApi(DEFAULT_CONFIG).coreTenantsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Domain"), "domain"),
            new TableColumn(msg("Default?"), "default"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Tenant(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Tenant) => {
                return [{ key: msg("Domain"), value: item.domain }];
            }}
            .usedBy=${(item: Tenant) => {
                return new CoreApi(DEFAULT_CONFIG).coreTenantsUsedByList({
                    tenantUuid: item.tenantUuid,
                });
            }}
            .delete=${(item: Tenant) => {
                return new CoreApi(DEFAULT_CONFIG).coreTenantsDestroy({
                    tenantUuid: item.tenantUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Tenant): TemplateResult[] {
        return [
            html`${item.domain}`,
            html`<ak-status-label ?good=${item._default}></ak-status-label>`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Tenant")} </span>
                    <ak-tenant-form slot="form" .instancePk=${item.tenantUuid}> </ak-tenant-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.TenantsTenant}
                    objectPk=${item.tenantUuid}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Tenant")} </span>
                <ak-tenant-form slot="form"> </ak-tenant-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}
