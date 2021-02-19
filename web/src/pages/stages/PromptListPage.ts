import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Prompt } from "../../api/Prompts";

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
        return Prompt.list({
            ordering: this.order,
            page: page,
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
            html`${item.field_key}`,
            html`${item.label}`,
            html`${item.type}`,
            html`${item.order}`,
            html`${item.promptstage_set.map((stage) => {
                return html`<li>${stage.name}</li>`;
            })}`,
            html`
            <ak-modal-button href="${Prompt.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Prompt.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${Prompt.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
