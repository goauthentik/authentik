import "#admin/groups/ak-group-form";
import "#admin/policies/PolicyBindingForm";
import "#admin/policies/ak-policy-wizard";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/users/UserForm";
import "#components/ak-status-label";
import "#elements/Tabs";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PolicyBindingCheckTarget, PolicyBindingCheckTargetToLabel } from "#common/policies/utils";

import { asInstanceInvokerByTagName, modalInvoker } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { GroupForm } from "#admin/groups/ak-group-form";
import { PolicyWizard } from "#admin/policies/ak-policy-wizard";
import { PolicyBindingForm, PolicyBindingNotice } from "#admin/policies/PolicyBindingForm";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { UserForm } from "#admin/users/UserForm";

import { ModelEnum, PoliciesApi, PolicyBinding } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList<T extends PolicyBinding = PolicyBinding> extends Table<T> {
    public static styles: CSSResult[] = [
        ...super.styles,
        css`
            /* Align policy engine description to left padding of the card title */
            .policy-desc {
                padding-left: var(--pf-global--spacer--lg);
            }
        `,
    ];

    @property({ type: String })
    public target: string | null = null;

    @property({ type: String })
    public policyEngineMode: string = "";

    @property({ type: Array })
    public allowedTypes: PolicyBindingCheckTarget[] = [
        PolicyBindingCheckTarget.Policy,
        PolicyBindingCheckTarget.Group,
        PolicyBindingCheckTarget.User,
    ];

    @property({ type: Array })
    public typeNotices: PolicyBindingNotice[] = [];

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "order";

    protected bindingEditForm = "ak-policy-binding-form";

    get allowedTypesLabel(): string {
        return this.allowedTypes.map((ct) => PolicyBindingCheckTargetToLabel(ct)).join(" / ");
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<T>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        }) as Promise<PaginatedResponse<T>>;
    }

    protected override rowLabel(item: PolicyBinding): string | null {
        return item.order?.toString() ?? null;
    }

    protected override columns: TableColumn[] = [
        [msg("Order"), "order"],
        [this.allowedTypesLabel],
        [msg("Enabled"), "enabled"],
        [msg("Timeout"), "timeout"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected getPolicyUserGroupRowLabel(item: PolicyBinding): string {
        if (item.policy) {
            return msg(str`Policy ${item.policyObj?.name}`);
        } else if (item.group) {
            return msg(str`Group ${item.groupObj?.name}`);
        } else if (item.user) {
            return msg(str`User ${item.userObj?.name || item.userObj?.username}`);
        }
        return msg("-");
    }

    protected getPolicyUserGroupRow(item: PolicyBinding): SlottedTemplateResult {
        const label = this.getPolicyUserGroupRowLabel(item);
        if (item.user) {
            return html` <a href=${`#/identity/users/${item.user}`}> ${label} </a> `;
        }
        if (item.group) {
            return html` <a href=${`#/identity/groups/${item.group}`}> ${label} </a> `;
        }
        return html`${label}`;
    }

    protected getObjectEditButton(item: PolicyBinding): SlottedTemplateResult {
        if (item.policyObj) {
            return html`<button
                type="button"
                class="pf-c-button pf-m-secondary"
                ${asInstanceInvokerByTagName(item.policyObj?.component, item.policyObj?.pk)}
            >
                ${msg("Edit Policy")}
            </button>`;
        }

        if (item.groupObj) {
            return html`<button
                class="pf-c-button pf-m-secondary"
                ${GroupForm.asInstanceInvoker(item.groupObj?.pk)}
            >
                ${msg("Edit Group")}
            </button>`;
        }

        if (item.userObj) {
            return html`<button
                class="pf-c-button pf-m-secondary"
                ${UserForm.asInstanceInvoker(item.userObj?.pk)}
            >
                ${msg("Edit User")}
            </button>`;
        }

        return null;
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-spinner-button .callAction=${this.refreshListener} class="pf-m-secondary">
                ${msg("Refresh")}</ak-spinner-button
            ><ak-forms-delete-bulk
                object-label=${msg("Policy binding(s)")}
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

    protected renderNewPolicyButton(): SlottedTemplateResult {
        return html`<button
            class="pf-c-button pf-m-primary"
            type="button"
            aria-description="${msg("Open the wizard to create a new policy.")}"
            ${modalInvoker(PolicyWizard, {
                showBindingPage: true,
                bindingTarget: this.target,
            })}
        >
            ${msg("Create or bind...")}
        </button>`;
    }

    protected override row(item: PolicyBinding): SlottedTemplateResult[] {
        return [
            html`<pre>${item.order}</pre>`,
            html`${this.getPolicyUserGroupRow(item)}`,
            html`<ak-status-label type="warning" ?good=${item.enabled}></ak-status-label>`,
            html`${item.timeout}`,
            html`<div class="ak-c-table__actions">
                ${this.getObjectEditButton(item)}
                <button
                    type="button"
                    class="pf-c-button pf-m-secondary"
                    ${modalInvoker(() => {
                        return StrictUnsafe<PolicyBindingForm>(this.bindingEditForm, {
                            instancePk: item.pk,
                            allowedTypes: this.allowedTypes,
                            typeNotices: this.typeNotices,
                            targetPk: this.target || "",
                        });
                    })}
                >
                    ${msg("Edit Binding")}
                </button>
                ${IconPermissionButton(this.getPolicyUserGroupRowLabel(item), {
                    model: ModelEnum.AuthentikPoliciesPolicybinding,
                    objectPk: item.pk,
                })}
            </div>`,
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module"
                ><span>${msg("No Policies bound.")}</span>
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div class="pf-c-form__group pf-m-action" slot="primary">
                    <legend class="sr-only">${msg("Policy actions")}</legend>
                    ${this.renderNewPolicyButton()}
                </div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): SlottedTemplateResult {
        return this.renderNewPolicyButton();
    }

    renderPolicyEngineMode() {
        const policyEngineMode = policyEngineModes.find(
            (pem) => pem.value === this.policyEngineMode,
        );
        if (policyEngineMode === undefined) {
            return nothing;
        }
        return html`${this.findSlotted("description")
                ? html`<p class="policy-desc">
                      <slot name="description"></slot>
                  </p>`
                : nothing}
            <p class="policy-desc">
                ${msg(str`The currently selected policy engine mode is ${policyEngineMode.label}:`)}
                ${policyEngineMode.description}
            </p>`;
    }

    renderToolbarContainer(): SlottedTemplateResult {
        return html`${this.renderPolicyEngineMode()} ${super.renderToolbarContainer()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-policies-list": BoundPoliciesList;
    }
}
