import "@goauthentik/admin/applications/entitlements/ApplicationEntitlementForm";
import "@goauthentik/admin/groups/GroupForm";
import "@goauthentik/admin/users/UserForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { PFSize } from "@goauthentik/common/enums";
import "@goauthentik/components/ak-status-label";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ApplicationEntitlement, CoreApi } from "@goauthentik/api";

@customElement("ak-application-entitlements-list")
export class ApplicationEntitlementsPage extends Table<ApplicationEntitlement> {
    @property()
    app?: string;

    checkbox = true;
    clearOnRefresh = true;

    order = "order";

    async apiEndpoint(): Promise<PaginatedResponse<ApplicationEntitlement>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsList({
            ...(await this.defaultEndpointConfig()),
            app: this.app || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("User / Group")),
            new TableColumn(msg("Actions")),
        ];
    }

    getPolicyUserGroupRowLabel(item: ApplicationEntitlement): string {
        if (item.group) {
            return msg(str`Group ${item.groupObj?.name}`);
        } else if (item.user) {
            return msg(str`User ${item.userObj?.name}`);
        } else {
            return msg("-");
        }
    }

    getPolicyUserGroupRow(item: ApplicationEntitlement): TemplateResult {
        const label = this.getPolicyUserGroupRowLabel(item);
        if (item.user) {
            return html` <a href=${`#/identity/users/${item.user}`}> ${label} </a> `;
        }
        if (item.group) {
            return html` <a href=${`#/identity/groups/${item.group}`}> ${label} </a> `;
        }
        return html`${label}`;
    }

    getObjectEditButton(item: ApplicationEntitlement): TemplateResult {
        if (item.group) {
            return html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Group")} </span>
                <ak-group-form slot="form" .instancePk=${item.groupObj?.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Edit Group")}
                </button>
            </ak-forms-modal>`;
        } else if (item.user) {
            return html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update User")} </span>
                <ak-user-form slot="form" .instancePk=${item.userObj?.pk}> </ak-user-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Edit User")}
                </button>
            </ak-forms-modal>`;
        } else {
            return html``;
        }
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Application entitlement(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: ApplicationEntitlement) => {
                return [
                    {
                        key: msg("Policy / User / Group"),
                        value: this.getPolicyUserGroupRowLabel(item),
                    },
                ];
            }}
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
            html`${this.getPolicyUserGroupRow(item)}`,
            html`${this.getObjectEditButton(item)}
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Entitlement")} </span>
                    <ak-application-entitlement-form
                        slot="form"
                        .instancePk=${item.pbmUuid}
                        targetPk=${ifDefined(this.app)}
                    >
                    </ak-application-entitlement-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit Entitlement")}
                    </button>
                </ak-forms-modal>`,
        ];
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
