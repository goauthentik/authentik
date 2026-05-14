import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/prompt/PromptForm";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PromptForm } from "#admin/stages/prompt/PromptForm";

import { ModelEnum, Prompt, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-prompt-list")
export class PromptListPage extends TablePage<Prompt> {
    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search for a prompt by name, field or type...");

    public override pageTitle = msg("Prompts");
    public override pageDescription = msg("Single Prompts that can be used for Prompt Stages.");
    public override pageIcon = "pf-icon pf-icon-plugged";

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Prompt>> {
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

    protected renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Prompt(s)")}
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

    protected override row(item: Prompt): SlottedTemplateResult[] {
        return [
            item.name,
            html`<code>${item.fieldKey}</code>`,
            item.type,
            item.order || msg("-"),
            html`${item.promptStagesObj.map((stage) => {
                return html`<li>${stage.name}</li>`;
            })}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PromptForm, item.pk, item.name, {
                    size: PFSize.XLarge,
                })}
                ${IconPermissionButton(item.name, {
                    model: ModelEnum.AuthentikStagesPromptPrompt,
                    objectPk: item.pk,
                })}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PromptForm, null, null, {
            size: PFSize.XLarge,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt-list": PromptListPage;
    }
}
