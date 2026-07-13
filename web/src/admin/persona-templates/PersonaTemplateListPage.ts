import "#admin/access-requests/PolicyBindingModelRequestRuleTable";
import "#admin/persona-templates/PersonaTemplateForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, RowType, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PersonaTemplateForm } from "#admin/persona-templates/PersonaTemplateForm";

import { PamApi, PersonaTemplate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

@customElement("ak-persona-template-list")
export class PersonaTemplateListPage extends TablePage<PersonaTemplate> {
    public override pageTitle = msg("Persona Templates");
    public override pageDescription = msg(
        "Templates users can self-request a Persona from. Actor providers/sources define which agents may act as any persona instantiated from a template.",
    );
    public override pageIcon = "pf-icon pf-icon-user";
    public override searchEnabled = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;

    protected override rowLabel(item: PersonaTemplate): string | null {
        return item.name;
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<PersonaTemplate>> {
        return aki(PamApi).pamPersonaTemplatesList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PersonaTemplateForm);
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Persona Template(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: PersonaTemplate) =>
                aki(PamApi).pamPersonaTemplatesUsedByList({ uuid: item.uuid! })}
            .delete=${(item: PersonaTemplate) =>
                aki(PamApi).pamPersonaTemplatesDestroy({ uuid: item.uuid! })}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderExpanded(item: PersonaTemplate): SlottedTemplateResult {
        return html`<div class="pf-c-form">
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Reviewer rules control who may approve a request to instantiate a Persona from this template.",
                )}
            </p>
            <ak-pbm-request-rule-table pbmUuid=${item.uuid}></ak-pbm-request-rule-table>
        </div>`;
    }

    protected override row(item: PersonaTemplate): RowType[] {
        return [
            html`${item.name}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PersonaTemplateForm, item.uuid, item.name)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-template-list": PersonaTemplateListPage;
    }
}
