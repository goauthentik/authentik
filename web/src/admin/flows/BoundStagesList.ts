import "#admin/flows/StageBindingForm";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/Tabs";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { modalInvoker } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { CustomFormElementTagName } from "#elements/forms/unsafe";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { StageBindingForm } from "#admin/flows/StageBindingForm";
import { AKStageWizard } from "#admin/stages/ak-stage-wizard";

import { FlowsApi, FlowStageBinding, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-bound-stages-list")
export class BoundStagesList extends Table<FlowStageBinding> {
    protected flowsAPI = new FlowsApi(DEFAULT_CONFIG);

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "order";

    @property({ type: String, useDefault: true })
    public target: string | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<FlowStageBinding>> {
        return this.flowsAPI.flowsBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    protected override rowLabel(item: FlowStageBinding): string {
        return `#${item.order} ${item.stageObj?.name || ""}`;
    }

    protected columns: TableColumn[] = [
        [msg("Order"), "order"],
        [msg("Name"), "stage__name"],
        [msg("Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Stage binding(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: FlowStageBinding) => {
                return [
                    { key: msg("Stage"), value: item.stageObj?.name || "" },
                    { key: msg("Stage type"), value: item.stageObj?.verboseName || "" },
                ];
            }}
            .usedBy=${(item: FlowStageBinding) => {
                return this.flowsAPI.flowsBindingsUsedByList({
                    fsbUuid: item.pk,
                });
            }}
            .delete=${(item: FlowStageBinding) => {
                return this.flowsAPI.flowsBindingsDestroy({
                    fsbUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: FlowStageBinding): SlottedTemplateResult[] {
        return [
            html`<pre>${item.order}</pre>`,
            item.stageObj?.name,
            item.stageObj?.verboseName,
            html`<div class="ak-c-table__actions">
                <button
                    type="button"
                    class="pf-c-button pf-m-secondary"
                    ${modalInvoker(() =>
                        StrictUnsafe<CustomFormElementTagName>(item.stageObj?.component, {
                            instancePk: item.stageObj?.pk,
                        }),
                    )}
                >
                    ${msg("Edit Stage")}
                </button>

                <button
                    type="button"
                    class="pf-c-button pf-m-secondary"
                    ${modalInvoker(StageBindingForm, { instancePk: item.pk })}
                >
                    ${msg("Edit Binding")}
                </button>
                ${IconPermissionButton(item.stageObj?.name || "", {
                    model: ModelEnum.AuthentikFlowsFlowstagebinding,
                    objectPk: item.pk,
                })}
            </div>`,
        ];
    }

    protected renderActions(): SlottedTemplateResult {
        return html`<button
            class="pf-c-button pf-m-primary"
            ${modalInvoker(AKStageWizard, {
                showBindingPage: true,
                bindingTarget: this.target,
            })}
        >
            ${msg("Bind...")}
        </button>`;
    }

    protected override renderExpanded(item: FlowStageBinding): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list
                .target=${item.policybindingmodelPtrId}
                .policyEngineMode=${item.policyEngineMode}
            >
                <span slot="description"
                    >${msg(
                        "These bindings control if this stage will be applied to the flow.",
                    )}</span
                >
            </ak-bound-policies-list>
        </div>`;
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-module">
                <span>${msg("No Stages bound")}</span>
                <div slot="body">${msg("No stages are currently bound to this flow.")}</div>
                <div slot="primary">${this.renderActions()}</div>
            </ak-empty-state>`,
        );
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return [this.renderActions(), super.renderToolbar()];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-stages-list": BoundStagesList;
    }
}
