import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { Prompt, StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-stage-prompt-list")
export class PromptListPage extends TablePage<Prompt> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Prompts");
    }
    pageDescription(): string {
        return gettext("Single Prompts that can be used for Prompt Stages.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-plugged");
    }

    @property()
    order = "order";

    apiEndpoint(page: number): Promise<AKResponse<Prompt>> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Field", "field_key"),
            new TableColumn("Label", "label"),
            new TableColumn("Type", "type"),
            new TableColumn("Order", "order"),
            new TableColumn("Stages"),
            new TableColumn(""),
        ];
    }

    row(item: Prompt): TemplateResult[] {
        return [
            html`${item.fieldKey}`,
            html`${item.label}`,
            html`${item.type}`,
            html`${item.order}`,
            html`${item.promptstageSet?.map((stage) => {
                return html`<li>${stage.name}</li>`;
            })}`,
            html`
            <ak-modal-button href="${AdminURLManager.stagePrompts(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Prompt")}
                .delete=${() => {
                    return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsDelete({
                        promptUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${AdminURLManager.stagePrompts("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
