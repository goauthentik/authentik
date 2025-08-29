import "#admin/groups/GroupForm";
import "#admin/policies/PolicyBindingForm";
import "#admin/policies/PolicyWizard";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/users/UserForm";
import "#components/ak-status-label";
import "#elements/Tabs";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { PolicyBindingNotice } from "#admin/policies/PolicyBindingForm";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { PolicyBindingCheckTarget, PolicyBindingCheckTargetToLabel } from "#admin/policies/utils";

import {
    PoliciesApi,
    PolicyBinding,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    @property()
    policyEngineMode: string = "";

    @property({ type: Array })
    allowedTypes: PolicyBindingCheckTarget[] = [
        PolicyBindingCheckTarget.policy,
        PolicyBindingCheckTarget.group,
        PolicyBindingCheckTarget.user,
    ];

    @property({ type: Array })
    typeNotices: PolicyBindingNotice[] = [];

    checkbox = true;
    clearOnRefresh = true;

    order = "order";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFSpacing);
    }

    get allowedTypesLabel(): string {
        return this.allowedTypes.map((ct) => PolicyBindingCheckTargetToLabel(ct)).join(" / ");
    }

    async apiEndpoint(): Promise<PaginatedResponse<PolicyBinding>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Order"), "order"),
            new TableColumn(this.allowedTypesLabel),
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
        }
        return msg("-");
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
        }
        return html``;
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
                        key: this.allowedTypesLabel,
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
            html`<ak-status-label type="warning" ?good=${item.enabled}></ak-status-label>`,
            html`${item.timeout}`,
            html` ${this.getObjectEditButton(item)}
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Binding")} </span>
                    <ak-policy-binding-form
                        slot="form"
                        .instancePk=${item.pk}
                        .allowedTypes=${this.allowedTypes}
                        .typeNotices=${this.typeNotices}
                        targetPk=${ifDefined(this.target)}
                    >
                    </ak-policy-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit Binding")}
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikPoliciesPolicybinding}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module"
                ><span>${msg("No Policies bound.")}</span>
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div slot="primary">
                    <ak-policy-wizard
                        createText=${msg("Create and bind Policy")}
                        showBindingPage
                        bindingTarget=${ifDefined(this.target)}
                    ></ak-policy-wizard>
                    <ak-forms-modal size=${PFSize.Medium}>
                        <span slot="submit"> ${msg("Create")} </span>
                        <span slot="header"> ${msg("Create Binding")} </span>
                        <ak-policy-binding-form
                            slot="form"
                            targetPk=${ifDefined(this.target)}
                            .allowedTypes=${this.allowedTypes}
                            .typeNotices=${this.typeNotices}
                        >
                        </ak-policy-binding-form>
                        <button slot="trigger" class="pf-c-button pf-m-primary">
                            ${msg("Bind existing policy/group/user")}
                        </button>
                    </ak-forms-modal>
                </div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): TemplateResult {
        return html`${this.allowedTypes.includes(PolicyBindingCheckTarget.policy)
                ? html`<ak-policy-wizard
                      createText=${msg("Create and bind Policy")}
                      showBindingPage
                      bindingTarget=${ifDefined(this.target)}
                  ></ak-policy-wizard>`
                : nothing}
            <ak-forms-modal size=${PFSize.Medium}>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Binding")} </span>
                <ak-policy-binding-form
                    slot="form"
                    targetPk=${ifDefined(this.target)}
                    .allowedTypes=${this.allowedTypes}
                    .typeNotices=${this.typeNotices}
                >
                </ak-policy-binding-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg(str`Bind existing ${this.allowedTypesLabel}`)}
                </button>
            </ak-forms-modal> `;
    }

    renderPolicyEngineMode() {
        const policyEngineMode = policyEngineModes.find(
            (pem) => pem.value === this.policyEngineMode,
        );
        if (policyEngineMode === undefined) {
            return nothing;
        }
        return html`<p class="pf-u-ml-md">
            ${msg(str`The currently selected policy engine mode is ${policyEngineMode.label}:`)}
            ${policyEngineMode.description}
        </p>`;
    }

    renderToolbarContainer(): TemplateResult {
        return html`${this.renderPolicyEngineMode()} ${super.renderToolbarContainer()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-policies-list": BoundPoliciesList;
    }
}
