import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, Tenant } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import { PFColor } from "../../elements/Label";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import "./TenantForm";

@customElement("ak-tenant-list")
export class TenantListPage extends TablePage<Tenant> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Tenants`;
    }
    pageDescription(): string {
        return t`Configure visual settings and defaults for different domains.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-tenant";
    }

    checkbox = true;

    @property()
    order = "domain";

    async apiEndpoint(page: number): Promise<AKResponse<Tenant>> {
        return new CoreApi(DEFAULT_CONFIG).coreTenantsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Domain`, "domain"),
            new TableColumn(t`Default?`, "default"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Tenant(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: Tenant) => {
                return [{ key: t`Domain`, value: item.domain }];
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Tenant): TemplateResult[] {
        return [
            html`${item.domain}`,
            html`<ak-label color=${item._default ? PFColor.Green : PFColor.Red}>
                ${item._default ? t`Yes` : t`No`}
            </ak-label>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Tenant`} </span>
                <ak-tenant-form slot="form" .instancePk=${item.tenantUuid}> </ak-tenant-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Tenant`} </span>
                <ak-tenant-form slot="form"> </ak-tenant-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }
}
