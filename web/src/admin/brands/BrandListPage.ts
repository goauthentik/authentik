import "@goauthentik/admin/brands/BrandForm";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Brand, CoreApi, RbacPermissionsAssignedByUsersListModelEnum } from "@goauthentik/api";

@customElement("ak-brand-list")
export class BrandListPage extends TablePage<Brand> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Brands");
    }
    pageDescription(): string {
        return msg("Configure visual settings and defaults for different domains.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-tenant";
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "domain";

    async apiEndpoint(): Promise<PaginatedResponse<Brand>> {
        return new CoreApi(DEFAULT_CONFIG).coreBrandsList(await this.defaultEndpointConfig());
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Domain"), "domain"),
            new TableColumn(msg("Brand name"), "branding_title"),
            new TableColumn(msg("Default?"), "default"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Brand(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Brand) => {
                return [{ key: msg("Domain"), value: item.domain }];
            }}
            .usedBy=${(item: Brand) => {
                return new CoreApi(DEFAULT_CONFIG).coreBrandsUsedByList({
                    brandUuid: item.brandUuid,
                });
            }}
            .delete=${(item: Brand) => {
                return new CoreApi(DEFAULT_CONFIG).coreBrandsDestroy({
                    brandUuid: item.brandUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Brand): TemplateResult[] {
        return [
            html`${item.domain}`,
            html`${item.brandingTitle}`,
            html`<ak-status-label ?good=${item._default}></ak-status-label>`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Brand")} </span>
                    <ak-brand-form slot="form" .instancePk=${item.brandUuid}> </ak-brand-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikBrandsBrand}
                    objectPk=${item.brandUuid}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Brand")} </span>
                <ak-brand-form slot="form"> </ak-brand-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-list": BrandListPage;
    }
}
