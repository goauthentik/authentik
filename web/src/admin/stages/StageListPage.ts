import "#admin/stages/register";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButtonByTagName, modalInvoker, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AKStageWizard } from "#admin/stages/ak-stage-wizard";
import { DuoDeviceImportForm } from "#admin/stages/authenticator_duo/DuoDeviceImportForm";

import { ModelEnum, Stage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    public override pageTitle = msg("Stages");
    public override pageDescription = msg(
        "Stages are single steps of a Flow that a user is guided through. A stage can only be executed from within a flow.",
    );
    public override pageIcon = "pf-icon pf-icon-plugged";
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "name";
    public override searchPlaceholder = msg("Search for a stage name, type, or flow...");

    protected override async apiEndpoint(): Promise<PaginatedResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Flows")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Stage(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllUsedByList({
                    stageUuid: item.pk,
                });
            }}
            .delete=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllDestroy({
                    stageUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected renderStageActions(stage: Stage): SlottedTemplateResult {
        if (stage.component !== "ak-stage-authenticator-duo-form") {
            return null;
        }

        return html`<button
            class="pf-c-button pf-m-plain"
            ${modalInvoker(DuoDeviceImportForm, { instancePk: stage.pk })}
        >
            <pf-tooltip position="top" content=${msg("Import devices")}>
                <i class="fas fa-file-import" aria-hidden="true"></i>
            </pf-tooltip>
        </button>`;
    }

    protected override row(item: Stage): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                <small>${item.verboseName}</small>`,
            html`<ul class="pf-c-list">
                ${item.flowSet?.map((flow) => {
                    return html`<li>
                        <a href="#/flow/flows/${flow.slug}">
                            <code>${flow.slug}</code>
                        </a>
                    </li>`;
                })}
            </ul>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButtonByTagName(item.component, item.pk)}
                ${IconPermissionButton(item.name, {
                    model: item.metaModelName as ModelEnum,
                    objectPk: item.pk,
                })}
                ${this.renderStageActions(item)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(AKStageWizard);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-list": StageListPage;
    }
}
