import "#admin/requests/RequestRuleBindingForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/policies/BoundPoliciesList";

import { aki } from "#common/api/client";

import { modalInvoker } from "#elements/dialogs";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { RequestRuleBindingForm } from "#admin/requests/RequestRuleBindingForm";

import { RequestRuleBinding, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-bound-request-rules-table")
export class BoundRequestRulesTable extends Table<RequestRuleBinding> {
    @property({ type: String })
    public target: string | null = null;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;

    protected bindingEditForm = "ak-request-rule-binding-form";

    protected override async apiEndpoint(): Promise<PaginatedResponse<RequestRuleBinding>> {
        return aki(RequestsApi).requestsRuleBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Rule")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Request rule binding(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: RequestRuleBinding) => {
                return [{ key: msg("Rule"), value: item.ruleObj?.name ?? "-" }];
            }}
            .usedBy=${(item: RequestRuleBinding) => {
                return aki(RequestsApi).requestsRuleBindingsUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: RequestRuleBinding) => {
                return aki(RequestsApi).requestsRuleBindingsDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected renderNewBindingButton(): SlottedTemplateResult {
        return html`<button
            type="button"
            class="pf-c-button pf-m-primary"
            ${modalInvoker(() => {
                return StrictUnsafe<RequestRuleBindingForm>(this.bindingEditForm, {
                    targetPk: this.target || "",
                });
            })}
        >
            ${msg("Bind existing rule")}
        </button>`;
    }

    protected override renderExpanded(item: RequestRuleBinding): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list
                .target=${item.pbmUuid}
                .policyEngineMode=${item.policyEngineMode}
            >
                <span slot="description"
                    >${msg(
                        "These bindings control which users/groups can request access to this object.",
                    )}</span
                >
            </ak-bound-policies-list>
        </div>`;
    }

    protected override row(item: RequestRuleBinding): SlottedTemplateResult[] {
        return [
            html`${item.ruleObj?.name ?? "-"}`,
            html`<div class="ak-c-table__actions">
                <button
                    type="button"
                    class="pf-c-button pf-m-secondary"
                    ${modalInvoker(() => {
                        return StrictUnsafe<RequestRuleBindingForm>(this.bindingEditForm, {
                            instancePk: item.uuid,
                            targetPk: this.target || "",
                        });
                    })}
                >
                    ${msg("Edit Binding")}
                </button>
            </div>`,
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module"
                ><span>${msg("No request rules bound.")}</span>
                <div slot="body">
                    ${msg("No request rules are currently bound to this object.")}
                </div>
                <div class="pf-c-form__group pf-m-action" slot="primary">
                    <legend class="sr-only">${msg("Request rule actions")}</legend>
                    ${this.renderNewBindingButton()}
                </div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): SlottedTemplateResult {
        return this.renderNewBindingButton();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-request-rules-table": BoundRequestRulesTable;
    }
}
