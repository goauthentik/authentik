import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { PoliciesApi, PolicyBinding } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import { PFSize } from "../../elements/Spinner";
import "../../elements/Tabs";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import { Table, TableColumn } from "../../elements/table/Table";
import "../groups/GroupForm";
import "../users/UserForm";
import "./PolicyBindingForm";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    @property({ type: Boolean })
    policyOnly = false;

    checkbox = true;

    async apiEndpoint(page: number): Promise<AKResponse<PolicyBinding>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            target: this.target || "",
            ordering: "order",
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Policy / User / Group`),
            new TableColumn(t`Enabled`, "enabled"),
            new TableColumn(t`Order`, "order"),
            new TableColumn(t`Timeout`, "timeout"),
            new TableColumn(t`Actions`),
        ];
    }

    getPolicyUserGroupRow(item: PolicyBinding): string {
        if (item.policy) {
            return t`Policy ${item.policyObj?.name}`;
        } else if (item.group) {
            return t`Group ${item.groupObj?.name}`;
        } else if (item.user) {
            return t`User ${item.userObj?.name}`;
        } else {
            return t`-`;
        }
    }

    getObjectEditButton(item: PolicyBinding): TemplateResult {
        if (item.policy) {
            return html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update ${item.policyObj?.name}`} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.policyObj?.pk,
                    }}
                    type=${ifDefined(item.policyObj?.component)}
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit Policy`}</button>
            </ak-forms-modal>`;
        } else if (item.group) {
            return html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Group`} </span>
                <ak-group-form slot="form" .instancePk=${item.groupObj?.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit Group`}</button>
            </ak-forms-modal>`;
        } else if (item.user) {
            return html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update User`} </span>
                <ak-user-form slot="form" .instancePk=${item.userObj?.pk}> </ak-user-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit User`}</button>
            </ak-forms-modal>`;
        } else {
            return html``;
        }
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Policy binding(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: PolicyBinding) => {
                return [
                    { key: t`Order`, value: item.order.toString() },
                    { key: t`Policy / User / Group`, value: this.getPolicyUserGroupRow(item) },
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: PolicyBinding): TemplateResult[] {
        return [
            html`${this.getPolicyUserGroupRow(item)}`,
            html`${item.enabled ? t`Yes` : t`No`}`,
            html`${item.order}`,
            html`${item.timeout}`,
            html` ${this.getObjectEditButton(item)}
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Binding`} </span>
                    <ak-policy-binding-form
                        slot="form"
                        .instancePk=${item.pk}
                        targetPk=${ifDefined(this.target)}
                        ?policyOnly=${this.policyOnly}
                    >
                    </ak-policy-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${t`Edit Binding`}
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state
            header=${t`No Policies bound.`}
            icon="pf-icon-module"
        >
            <div slot="body">${t`No policies are currently bound to this object.`}</div>
            <div slot="primary">
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="submit"> ${t`Create`} </span>
                    <span slot="header"> ${t`Create Binding`} </span>
                    <ak-policy-binding-form
                        slot="form"
                        targetPk=${ifDefined(this.target)}
                        ?policyOnly=${this.policyOnly}
                    >
                    </ak-policy-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-primary">
                        ${t`Create Binding`}
                    </button>
                </ak-forms-modal>
            </div>
        </ak-empty-state>`);
    }

    renderToolbar(): TemplateResult {
        return html` <ak-forms-modal size=${PFSize.Medium}>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Binding`} </span>
                <ak-policy-binding-form
                    slot="form"
                    targetPk=${ifDefined(this.target)}
                    ?policyOnly=${this.policyOnly}
                >
                </ak-policy-binding-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${t`Create Binding`}
                </button>
            </ak-forms-modal>
            <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-secondary pf-c-button pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create Policy`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(
                        new PoliciesApi(DEFAULT_CONFIG).policiesAllTypesList().then((types) => {
                            return types.map((type) => {
                                return html`<li>
                                    <ak-forms-modal>
                                        <span slot="submit"> ${t`Create`} </span>
                                        <span slot="header"> ${t`Create ${type.name}`} </span>
                                        <ak-proxy-form slot="form" type=${type.component}>
                                        </ak-proxy-form>
                                        <button slot="trigger" class="pf-c-dropdown__menu-item">
                                            ${type.name}<br />
                                            <small>${type.description}</small>
                                        </button>
                                    </ak-forms-modal>
                                </li>`;
                            });
                        }),
                        html`<ak-spinner></ak-spinner>`,
                    )}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }
}
