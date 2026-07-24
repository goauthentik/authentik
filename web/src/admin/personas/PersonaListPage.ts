import "#admin/rbac/ObjectPermissionModal";
import "#admin/requests/PersonaForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { aki } from "#common/api/client";

import { ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PersonaForm } from "#admin/requests/PersonaForm";

import { Persona, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-persona-list")
export class PersonaListPage extends TablePage<Persona> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a persona...");
    public override pageTitle = msg("Personas");
    public override pageDescription = msg(
        "Admin-provisioned delegate identities that access can be requested and granted for, separately from their parent user.",
    );
    public override pageIcon = "pf-icon pf-icon-user";

    public override order = "username";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<Persona>> {
        return aki(RequestsApi).requestsPersonasList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Parent")],
        [msg("Expires"), "expires"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            object-label=${msg("Persona(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: Persona) => {
                return aki(RequestsApi).requestsPersonasDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Persona): SlottedTemplateResult[] {
        return [
            html`<div>${item.username}</div>
                <small>${item.name}</small>`,
            html`<a href="#/identity/users/${item.parent.pk}">
                <div>${item.parent.username}</div>
                <small>${item.parent.name}</small>
            </a>`,
            item.expiring && item.expires ? Timestamp(item.expires) : msg("Never"),
            html`<ak-forms-delete-bulk
                object-label=${msg("Persona")}
                .objects=${[item]}
                .delete=${(persona: Persona) => {
                    return aki(RequestsApi).requestsPersonasDestroy({
                        id: persona.pk,
                    });
                }}
            >
                <button slot="trigger" class="pf-c-button pf-m-danger pf-m-small">
                    ${msg("Delete")}
                </button>
            </ak-forms-delete-bulk>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PersonaForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-list": PersonaListPage;
    }
}
