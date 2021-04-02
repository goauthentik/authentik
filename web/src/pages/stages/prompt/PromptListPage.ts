import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../../api/Client";
import { TablePage } from "../../../elements/table/TablePage";

import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/ModalForm";
import "./PromptForm";
import { TableColumn } from "../../../elements/table/Table";
import { PAGE_SIZE } from "../../../constants";
import { Prompt, StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

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
        return "pf-icon pf-icon-plugged";
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
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Prompt")}
                </span>
                <ak-prompt-form slot="form" .prompt=${item}>
                </ak-prompt-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
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
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Prompt")}
            </span>
            <ak-prompt-form slot="form">
            </ak-prompt-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
