import "#admin/access-requests/PolicyBindingModelRequestRuleForm";
import "#elements/forms/DeleteBulkForm";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, RowType, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyBindingModelRequestRuleForm } from "#admin/access-requests/PolicyBindingModelRequestRuleForm";

import { PamApi, PolicyBindingModelRequestRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-pbm-request-rule-table")
export class PolicyBindingModelRequestRuleTable extends Table<PolicyBindingModelRequestRule> {
    public override checkbox = true;

    @property()
    pbmUuid?: string;

    protected async apiEndpoint(): Promise<
        PaginatedResponse<PolicyBindingModelRequestRule, object>
    > {
        return aki(PamApi).pamRequestRulesList({
            ...(await this.defaultEndpointConfig()),
            pbmPbmUuid: this.pbmUuid,
        });
    }

    protected columns: TableColumn[] = [[msg("Name"), "name"], [msg("Actions")]];

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PolicyBindingModelRequestRuleForm, {
            pbmUuid: this.pbmUuid,
        });
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Request Rule(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: PolicyBindingModelRequestRule) => {
                return aki(PamApi).pamRequestRulesUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: PolicyBindingModelRequestRule) => {
                return aki(PamApi).pamRequestRulesDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected row(item: PolicyBindingModelRequestRule): RowType[] {
        return [
            html`${item.name}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PolicyBindingModelRequestRuleForm, item.uuid)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-table": PolicyBindingModelRequestRuleTable;
    }
}
