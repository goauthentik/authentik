import "#admin/brands/BrandForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Brand, CoreApi, RbacPermissionsAssignedByUsersListModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-brand-list")
export class BrandListPage extends TablePage<Brand> {
    protected override searchEnabled = true;
    protected override entityLabel = {
        singular: msg("Brand", { id: "entity.brand.singular" }),
        plural: msg("Brands", { id: "entity.brand.plural" }),
    };
    protected get searchPlaceholder() {
        return msg("Search by domain or brand name...", {
            id: "search.placeholder.brand-list",
        });
    }

    public pageDescription = msg("Configure visual settings and defaults for different domains.");
    public pageIcon = "pf-icon pf-icon-tenant";

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "domain";

    async apiEndpoint(): Promise<PaginatedResponse<Brand>> {
        return new CoreApi(DEFAULT_CONFIG).coreBrandsList(await this.defaultEndpointConfig());
    }

    protected override rowLabel(item: Brand): string | null {
        return item.domain ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Domain", { id: "column.domain" }), "domain"],
        [msg("Brand name", { id: "column.brand-name" }), "branding_title"],
        [msg("Default?", { id: "column.default-question-mark" }), "default"],
        [
            msg("Actions", { id: "column.actions" }),
            null,
            msg("Row Actions", { id: "column.row-actions" }),
        ],
    ];

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

    row(item: Brand): SlottedTemplateResult[] {
        return [
            html`${item.domain}`,
            html`${item.brandingTitle}`,
            html`<ak-status-label ?good=${item._default}></ak-status-label>`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${this.updateEntityLabel}</span>
                    <span slot="header">${msg("Update Brand")}</span>
                    <ak-brand-form slot="form" .instancePk=${item.brandUuid}> </ak-brand-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikBrandsBrand}
                    objectPk=${item.brandUuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${this.createEntityLabel}</span>
                <span slot="header">${this.newEntityActionLabel}</span>
                <ak-brand-form slot="form"> </ak-brand-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${this.newEntityActionLabel}
                </button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-list": BrandListPage;
    }
}
