import "@goauthentik/admin/groups/GroupForm";
import "@goauthentik/admin/policies/PolicyBindingForm";
import "@goauthentik/admin/policies/PolicyWizard";
import "@goauthentik/admin/users/UserForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import { PFSize } from "@goauthentik/elements/Spinner";
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

import { PoliciesApi, PolicyBinding } from "@goauthentik/api";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    @property({ type: Boolean })
    policyOnly = false;

    checkbox = true;

    async apiEndpoint(page: number): Promise<PaginatedResponse<PolicyBinding>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            target: this.target || "",
            ordering: "order",
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Order"), "order"),
            new TableColumn(msg("Policy / User / Group")),
            new TableColumn(msg("Enabled"), "enabled"),
            new TableColumn(msg("Timeout"), "timeout"),
            new TableColumn(msg("Actions")),
        ];
    }

    getPolicyUserGroupRowLabel(item: PolicyBinding): string {
        if (item.policy) {
            return msg(str`Policy ${item.policyObj?.name}`);
        } else if (item.group) {
            return msg(str`Group ${item.groupObj?.name}`);
        } else if (item.user) {
            return msg(str`User ${item.userObj?.name}`);
        } else {
            return msg("-");
        }
    }

    getPolicyUserGroupRow(item: PolicyBinding): TemplateResult {
        const label = this.getPolicyUserGroupRowLabel(item);
        if (item.user) {
            return html` <a href=${`#/identity/users/${item.user}`}> ${label} </a> `;
        }
        if (item.group) {
            return html` <a href=${`#/identity/groups/${item.group}`}> ${label} </a> `;
        }
        return html`${label}`;
    }

    getObjectEditButton(item: PolicyBinding): TemplateResult {
        if (item.policy) {
            return html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg(str`Update ${item.policyObj?.name}`)} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.policyObj?.pk,
                    }}
                    type=${ifDefined(item.policyObj?.component)}
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Edit Policy")}
                </button>
            </ak-forms-modal>`;
        } else if (item.group) {
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
            objectLabel=${msg("Policy binding(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: PolicyBinding) => {
                return [
                    { key: msg("Order"), value: item.order.toString() },
                    {
                        key: msg("Policy / User / Group"),
                        value: this.getPolicyUserGroupRowLabel(item),
                    },
                ];
            }}
            .usedBy=${(item: PolicyBinding) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsUsedByList({
                    policyBindingUuid: item.pk,
                });
            }}
            .delete=${(item: PolicyBinding) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsDestroy({
                    policyBindingUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: PolicyBinding): TemplateResult[] {
        return [
            html`<pre>${item.order}</pre>`,
            html`${this.getPolicyUserGroupRow(item)}`,
            html` <ak-label color=${item.enabled ? PFColor.Green : PFColor.Orange}>
                ${item.enabled ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${item.timeout}`,
            html` ${this.getObjectEditButton(item)}
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Binding")} </span>
                    <ak-policy-binding-form
                        slot="form"
                        .instancePk=${item.pk}
                        targetPk=${ifDefined(this.target)}
                        ?policyOnly=${this.policyOnly}
                    >
                    </ak-policy-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit Binding")}
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state header=${msg("No Policies bound.")} icon="pf-icon-module">
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div slot="primary">
                    <ak-forms-modal size=${PFSize.Medium}>
                        <span slot="submit"> ${msg("Create")} </span>
                        <span slot="header"> ${msg("Create Binding")} </span>
                        <ak-policy-binding-form
                            slot="form"
                            targetPk=${ifDefined(this.target)}
                            ?policyOnly=${this.policyOnly}
                        >
                        </ak-policy-binding-form>
                        <button slot="trigger" class="pf-c-button pf-m-primary">
                            ${msg("Create Binding")}
                        </button>
                    </ak-forms-modal>
                </div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): TemplateResult {
        return html`<ak-policy-wizard
                createText=${msg("Create and bind Policy")}
                ?showBindingPage=${true}
                bindingTarget=${ifDefined(this.target)}
            ></ak-policy-wizard>
            <ak-forms-modal size=${PFSize.Medium}>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Binding")} </span>
                <ak-policy-binding-form
                    slot="form"
                    targetPk=${ifDefined(this.target)}
                    ?policyOnly=${this.policyOnly}
                >
                </ak-policy-binding-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Bind existing policy")}
                </button>
            </ak-forms-modal> `;
    }
}
