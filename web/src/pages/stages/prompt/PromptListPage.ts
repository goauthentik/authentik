import { t } from "@lingui/macro";
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
        return t`Prompts`;
    }
    pageDescription(): string {
        return t`Single Prompts that can be used for Prompt Stages.`;
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
            new TableColumn(t`Field`, "field_key"),
            new TableColumn(t`Label`, "label"),
            new TableColumn(t`Type`, "type"),
            new TableColumn(t`Order`, "order"),
            new TableColumn(t`Stages`),
            new TableColumn("Actions"),
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
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Prompt`} </span>
                    <ak-prompt-form slot="form" .instancePk=${item.pk}> </ak-prompt-form>
                    <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Edit`}</button>
                </ak-forms-modal>
                <ak-forms-delete
                    .obj=${item}
                    objectLabel=${t`Prompt`}
                    .usedBy=${() => {
                        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsUsedByList({
                            promptUuid: item.pk,
                        });
                    }}
                    .delete=${() => {
                        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsDestroy({
                            promptUuid: item.pk,
                        });
                    }}
                >
                    <button slot="trigger" class="pf-c-button pf-m-danger">${t`Delete`}</button>
                </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Prompt`} </span>
                <ak-prompt-form slot="form"> </ak-prompt-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
