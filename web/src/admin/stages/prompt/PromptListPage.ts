import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/prompt/PromptForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import { Prompt, RbacPermissionsAssignedByUsersListModelEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-prompt-list")
export class PromptListPage extends TablePage<Prompt> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Prompts");
    }
    pageDescription(): string {
        return msg("Single Prompts that can be used for Prompt Stages.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-plugged";
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Prompt>> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList(
            await this.defaultEndpointConfig(),
        );
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Field"), "field_key"),
            new TableColumn(msg("Type"), "type"),
            new TableColumn(msg("Order"), "order"),
            new TableColumn(msg("Stages")),
            new TableColumn(msg("Actions")),
        ];
    }

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

    row(item: Prompt): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<code>${item.fieldKey}</code>`,
            html`${item.type}`,
            html`${item.order}`,
            html`${item.promptstageSet?.map((stage) => {
                return html`<li>${stage.name}</li>`;
            })}`,
            html`<ak-forms-modal size=${PFSize.XLarge}>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Prompt")} </span>
                    <ak-prompt-form slot="form" .instancePk=${item.pk}> </ak-prompt-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikStagesPromptPrompt}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal> `,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal size=${PFSize.XLarge}>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Prompt")} </span>
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
