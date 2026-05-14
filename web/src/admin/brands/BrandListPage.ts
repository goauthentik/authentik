import "#admin/brands/BrandForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { BrandForm } from "#admin/brands/BrandForm";

import { Brand, CoreApi, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-brand-list")
export class BrandListPage extends TablePage<Brand> {
    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search by domain or brand name...");
    public pageTitle = msg("Brands");
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
        [msg("Domain"), "domain"],
        [msg("Brand name"), "branding_title"],
        [msg("Default?"), "default"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Brand(s)")}
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

    protected override row(item: Brand): SlottedTemplateResult[] {
        return [
            item.domain,
            item.brandingTitle || msg("-"),
            html`<ak-status-label ?good=${item._default} type="neutral"></ak-status-label>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(BrandForm, item.brandUuid, item.brandingTitle)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikBrandsBrand}
                    objectPk=${item.brandUuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(BrandForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-list": BrandListPage;
    }
}
