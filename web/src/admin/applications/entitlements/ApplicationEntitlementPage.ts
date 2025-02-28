import "@goauthentik/admin/applications/entitlements/ApplicationEntitlementForm";
import "@goauthentik/admin/policies/BoundPoliciesList";
import { PolicyBindingCheckTarget } from "@goauthentik/admin/policies/utils";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { PFSize } from "@goauthentik/common/enums.js";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    ApplicationEntitlement,
    CoreApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

@customElement("ak-application-entitlements-list")
export class ApplicationEntitlementsPage extends Table<ApplicationEntitlement> {
    @property()
    app?: string;

    checkbox = true;
    clearOnRefresh = true;
    expandable = true;

    order = "order";

    async apiEndpoint(): Promise<PaginatedResponse<ApplicationEntitlement>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsList({
            ...(await this.defaultEndpointConfig()),
            app: this.app || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name"), "name"), new TableColumn(msg("Actions"))];
    }

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

    row(item: ApplicationEntitlement): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Entitlement")} </span>
                    <ak-application-entitlement-form
                        slot="form"
                        .instancePk=${item.pbmUuid}
                        targetPk=${ifDefined(this.app)}
                    >
                    </ak-application-entitlement-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikCoreApplicationentitlement}
                    objectPk=${item.pbmUuid}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderExpanded(item: ApplicationEntitlement): TemplateResult {
        return html` <td></td>
            <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-c-content">
                        <p>
                            ${msg(
                                "These bindings control which users have access to this entitlement.",
                            )}
                        </p>
                        <ak-bound-policies-list
                            .target=${item.pbmUuid}
                            .allowedTypes=${[
                                PolicyBindingCheckTarget.group,
                                PolicyBindingCheckTarget.user,
                            ]}
                        >
                        </ak-bound-policies-list>
                    </div>
                </div>
            </td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state
                header=${msg("No app entitlements created.")}
                icon="pf-icon-module"
            >
                <div slot="body">
                    ${msg(
                        "This application does currently not have any application entitlement defined.",
                    )}
                </div>
                <div slot="primary"></div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal size=${PFSize.Medium}>
            <span slot="submit"> ${msg("Create")} </span>
            <span slot="header"> ${msg("Create Entitlement")} </span>
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
