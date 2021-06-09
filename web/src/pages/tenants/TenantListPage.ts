import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/DeleteForm";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Tenant } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ModalForm";
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

    @property()
    order = "domain";

    apiEndpoint(page: number): Promise<AKResponse<Tenant>> {
        return new CoreApi(DEFAULT_CONFIG).coreTenantsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Domain`, "domain"),
            new TableColumn(t`Default?`, "default"),
            new TableColumn(""),
        ];
    }

    row(item: Tenant): TemplateResult[] {
        return [
            html`${item.domain}`,
            html`${item._default ? t`Yes` : t`No`}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update Tenant`}
                </span>
                <ak-tenant-form slot="form" .instancePk=${item.tenantUuid}>
                </ak-tenant-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Tenant`}
                .usedBy=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreTenantsUsedByList({
                        tenantUuid: item.tenantUuid
                    });
                }}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreTenantsDestroy({
                        tenantUuid: item.tenantUuid
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete`}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create Tenant`}
            </span>
            <ak-tenant-form slot="form">
            </ak-tenant-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
