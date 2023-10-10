import "@goauthentik/admin/stages/prompt/PromptForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/ObjectPermissionModal";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Prompt, RbacPermissionsAssignedByUsersListModelEnum, StagesApi } from "@goauthentik/api";

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

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Prompt>> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
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
            html`<ak-forms-modal>
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
                    model=${RbacPermissionsAssignedByUsersListModelEnum.StagesPromptPrompt}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal> `,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Prompt")} </span>
                <ak-prompt-form slot="form"> </ak-prompt-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}
