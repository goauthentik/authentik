import "#admin/access-requests/PolicyBindingModelRequestRuleForm";

import { aki } from "#common/api/client";

import { ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, RowType, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PolicyBindingModelRequestRuleForm } from "#admin/access-requests/PolicyBindingModelRequestRuleForm";

import { PamApi, PolicyBindingModelRequestRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-pbm-request-rule-table")
export class PolicyBindingModelRequestRuleTable extends Table<PolicyBindingModelRequestRule> {
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

    protected columns: TableColumn[] = [[msg("Name"), "name"]];

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PolicyBindingModelRequestRuleForm, {
            pbmUuid: this.pbmUuid,
        });
    }

    protected row(item: PolicyBindingModelRequestRule): RowType[] {
        return [html`${item.name}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-table": PolicyBindingModelRequestRuleTable;
    }
}
