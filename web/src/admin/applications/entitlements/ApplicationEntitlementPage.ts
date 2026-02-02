import "#admin/applications/entitlements/ApplicationEntitlementForm";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/Tabs";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyBindingCheckTarget } from "#admin/policies/utils";

import {
    ApplicationEntitlement,
    CoreApi,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-entitlements-list")
export class ApplicationEntitlementsPage extends Table<ApplicationEntitlement> {
    @property()
    app?: string;

    checkbox = true;
    clearOnRefresh = true;
    expandable = true;

    order = "order";

    protected override searchEnabled = true;

    async apiEndpoint(): Promise<PaginatedResponse<ApplicationEntitlement>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsList({
            ...(await this.defaultEndpointConfig()),
            app: this.app || "",
        });
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Application entitlement(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: ApplicationEntitlement) => {
                return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsUsedByList({
                    pbmUuid: item.pbmUuid || "",
                });
            }}
            .delete=${(item: ApplicationEntitlement) => {
                return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsDestroy({
                    pbmUuid: item.pbmUuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: ApplicationEntitlement): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Entitlement")}</span>
                    <ak-application-entitlement-form
                        slot="form"
                        .instancePk=${item.pbmUuid}
                        targetPk=${ifDefined(this.app)}
                    >
                    </ak-application-entitlement-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikCoreApplicationentitlement}
                    objectPk=${item.pbmUuid}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderExpanded(item: ApplicationEntitlement): TemplateResult {
        return html`<div class="pf-c-content">
            <p>${msg("These bindings control which users have access to this entitlement.")}</p>
            <ak-bound-policies-list
                .target=${item.pbmUuid}
                .allowedTypes=${[PolicyBindingCheckTarget.Group, PolicyBindingCheckTarget.User]}
            >
            </ak-bound-policies-list>
        </div>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module"
                ><span>${msg("No app entitlements created.")}</span>

                <div slot="body">
                    ${msg(
                        "This application does currently not have any application entitlements defined.",
                    )}
                </div>
                <div slot="primary"></div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal size=${PFSize.Medium}>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("Create Entitlement")}</span>
            <ak-application-entitlement-form slot="form" targetPk=${ifDefined(this.app)}>
            </ak-application-entitlement-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${msg("Create entitlement")}
            </button>
        </ak-forms-modal> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-roles-list": ApplicationEntitlementsPage;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-entitlements-list": ApplicationEntitlementsPage;
    }
}
