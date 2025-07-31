import "#admin/brands/BrandPolicyForm";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/policies/BoundPoliciesList";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import {
    BrandPolicy,
    CoreApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-brand-policy-list")
export class BrandPolicyListPage extends TablePage<BrandPolicy> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Brand Policies");
    }
    pageDescription(): string {
        return msg("Configure policies to run on every backend request.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-tenant";
    }

    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "domain";

    async apiEndpoint(): Promise<PaginatedResponse<BrandPolicy>> {
        return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesList(
            await this.defaultEndpointConfig(),
        );
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name"), "name"), new TableColumn(msg("Actions"))];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Brand Policies")}
            .objects=${this.selectedElements}
            .usedBy=${(item: BrandPolicy) => {
                return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesUsedByList({
                    pbmUuid: item.pbmUuid,
                });
            }}
            .delete=${(item: BrandPolicy) => {
                return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesDestroy({
                    pbmUuid: item.pbmUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: BrandPolicy): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Brand Policy")} </span>
                    <ak-brand-policy-form slot="form" .instancePk=${item.pbmUuid}>
                    </ak-brand-policy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikBrandsBrandpolicy}
                    objectPk=${item.pbmUuid}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Brand Policy")} </span>
                <ak-brand-policy-form slot="form"> </ak-brand-policy-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }

    renderExpanded(item: BrandPolicy): TemplateResult {
        return html` <td></td>
            <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-c-content">
                        <p>
                            ${msg(
                                "Bound policies are ran on every call to the given path(s) of the given brand.",
                            )}
                        </p>
                        <ak-bound-policies-list
                            .target=${item.policybindingmodelPtrId}
                            .policyEngineMode=${item.policyEngineMode}
                        >
                        </ak-bound-policies-list>
                    </div>
                </div>
            </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-policy-list": BrandPolicyListPage;
    }
}
