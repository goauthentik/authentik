import "#admin/personas/PersonaForm";
import "#components/ak-status-label";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, RowType, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PersonaForm } from "#admin/personas/PersonaForm";

import { PamApi, Persona } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

@customElement("ak-persona-list")
export class PersonaListPage extends TablePage<Persona> {
    public override pageTitle = msg("Personas");
    public override pageDescription = msg(
        "Pre-provisioned agent identities that can be granted access to applications on behalf of a user.",
    );
    public override pageIcon = "pf-icon pf-icon-user";
    public override searchEnabled = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override order = "expires";

    protected override rowLabel(item: Persona): string | null {
        return item.username;
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<Persona>> {
        return aki(PamApi).pamPersonasList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Identifier"), "username"],
        [msg("User"), "parent"],
        [msg("Expiring"), "expiring"],
        [msg("Expires"), "expires"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PersonaForm);
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Persona(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Persona) => [{ key: msg("Identifier"), value: item.username }]}
            .delete=${(item: Persona) =>
                aki(PamApi).pamPersonasDestroy({
                    id: item.pk,
                })}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Persona): RowType[] {
        return [
            html`<span class="pf-m-monospace">${item.username}</span>`,
            html`<a href="#/identity/users/${item.parent?.pk}">${item.parent?.username}</a>`,
            html`<ak-status-label ?good=${item.expiring}></ak-status-label>`,
            item.expiring && item.expires ? Timestamp(item.expires) : html`${msg("-")}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PersonaForm, item.pk, item.username)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-list": PersonaListPage;
    }
}
