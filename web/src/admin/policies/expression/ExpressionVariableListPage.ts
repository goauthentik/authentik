import "@goauthentik/admin/policies/expression/ExpressionVariableForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/ConfirmationForm";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ExpressionVariable, PoliciesApi } from "@goauthentik/api";

@customElement("ak-expression-variable-list")
export class ExpressionVariableListPage extends TablePage<ExpressionVariable> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Variables");
    }
    pageDescription(): string {
        return msg("Variables that can be passed on to expressions.");
    }
    pageIcon(): string {
        // TODO: ask Jens what to put here
        return "pf-icon pf-icon-infrastructure";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<ExpressionVariable>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name"), "name"), new TableColumn(msg("Actions"))];
    }

    row(item: ExpressionVariable): TemplateResult[] {
        let managedSubText = msg("Managed by authentik");
        if (item.managed && item.managed.startsWith("goauthentik.io/variables/discovered")) {
            managedSubText = msg("Managed by authentik (Discovered)");
        }
        return [
            html`<div>${item.name}</div>
                ${item.managed ? html`<small>${managedSubText}</small>` : html``}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Variable")} </span>
                <ak-expression-variable-form slot="form" .instancePk=${item.id}>
                </ak-expression-variable-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Variable / Variables")}
            .objects=${this.selectedElements}
            .usedBy=${(item: ExpressionVariable) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesUsedByList({
                    id: item.id,
                });
            }}
            .delete=${(item: ExpressionVariable) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Variable")} </span>
                <ak-expression-variable-form slot="form"> </ak-expression-variable-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}
