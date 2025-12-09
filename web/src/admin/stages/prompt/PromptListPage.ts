import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/prompt/PromptForm";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Prompt, RbacPermissionsAssignedByRolesListModelEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-prompt-list")
export class PromptListPage extends TablePage<Prompt> {
    protected override searchEnabled = true;
    public pageTitle = msg("Prompts");
    public pageDescription = msg("Single Prompts that can be used for Prompt Stages.");
    public pageIcon = "pf-icon pf-icon-plugged";

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Prompt>> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Field"), "field_key"],
        [msg("Type"), "type"],
        [msg("Order"), "order"],
        [msg("Stages")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Prompt(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Prompt) => {
                return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsUsedByList({
                    promptUuid: item.pk,
                });
            }}
            .delete=${(item: Prompt) => {
                return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsDestroy({
                    promptUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Prompt): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<code>${item.fieldKey}</code>`,
            html`${item.type}`,
            html`${item.order}`,
            html`${item.promptStagesObj.map((stage) => {
                return html`<li>${stage.name}</li>`;
            })}`,
            html`<ak-forms-modal size=${PFSize.XLarge}>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Prompt")}</span>
                    <ak-prompt-form slot="form" .instancePk=${item.pk}> </ak-prompt-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikStagesPromptPrompt}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal> `,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal size=${PFSize.XLarge}>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Prompt")}</span>
                <ak-prompt-form slot="form"> </ak-prompt-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt-list": PromptListPage;
    }
}
