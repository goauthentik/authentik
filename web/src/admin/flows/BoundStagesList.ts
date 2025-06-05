import "#elements/Tabs";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "#admin/flows/StageBindingForm";
import "#admin/policies/BoundPoliciesList";
import "#admin/stages/StageWizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import {
    FlowStageBinding,
    FlowsApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-bound-stages-list")
export class BoundStagesList extends Table<FlowStageBinding> {
    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    order = "order";

    @property()
    target?: string;

    async apiEndpoint(): Promise<PaginatedResponse<FlowStageBinding>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Order"), "order"),
            new TableColumn(msg("Name"), "stage__name"),
            new TableColumn(msg("Type")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Stage binding(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: FlowStageBinding) => {
                return [
                    { key: msg("Stage"), value: item.stageObj?.name || "" },
                    { key: msg("Stage type"), value: item.stageObj?.verboseName || "" },
                ];
            }}
            .usedBy=${(item: FlowStageBinding) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsBindingsUsedByList({
                    fsbUuid: item.pk,
                });
            }}
            .delete=${(item: FlowStageBinding) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsBindingsDestroy({
                    fsbUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: FlowStageBinding): TemplateResult[] {
        return [
            html`<pre>${item.order}</pre>`,
            html`${item.stageObj?.name}`,
            html`${item.stageObj?.verboseName}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg(str`Update ${item.stageObj?.verboseName}`)} </span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.stage,
                        }}
                        type=${ifDefined(item.stageObj?.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit Stage")}
                    </button>
                </ak-forms-modal>
                <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Stage binding")} </span>
                    <ak-stage-binding-form slot="form" .instancePk=${item.pk}>
                    </ak-stage-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit Binding")}
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikFlowsFlowstagebinding}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>`,
        ];
    }

    renderExpanded(item: FlowStageBinding): TemplateResult {
        return html` <td></td>
            <td role="cell" colspan="4">
                <div class="pf-c-table__expandable-row-content">
                    <div class="pf-c-content">
                        <p>
                            ${msg(
                                "These bindings control if this stage will be applied to the flow.",
                            )}
                        </p>
                        <ak-bound-policies-list .target=${item.policybindingmodelPtrId}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state header=${msg("No Stages bound")} icon="pf-icon-module">
                <div slot="body">${msg("No stages are currently bound to this flow.")}</div>
                <div slot="primary">
                    <ak-stage-wizard
                        createText=${msg("Create and bind Stage")}
                        ?showBindingPage=${true}
                        bindingTarget=${ifDefined(this.target)}
                    ></ak-stage-wizard>
                    <ak-forms-modal>
                        <span slot="submit"> ${msg("Create")} </span>
                        <span slot="header"> ${msg("Create Stage binding")} </span>
                        <ak-stage-binding-form slot="form" targetPk=${ifDefined(this.target)}>
                        </ak-stage-binding-form>
                        <button slot="trigger" class="pf-c-button pf-m-primary">
                            ${msg("Bind existing stage")}
                        </button>
                    </ak-forms-modal>
                </div>
            </ak-empty-state>`,
        );
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-stage-wizard
                createText=${msg("Create and bind Stage")}
                ?showBindingPage=${true}
                bindingTarget=${ifDefined(this.target)}
            ></ak-stage-wizard>
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Stage binding")} </span>
                <ak-stage-binding-form slot="form" targetPk=${ifDefined(this.target)}>
                </ak-stage-binding-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Bind existing stage")}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-stages-list": BoundStagesList;
    }
}
