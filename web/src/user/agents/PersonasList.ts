import "#components/ak-status-label";
import "#elements/forms/DeleteBulkForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PamApi, Persona } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-user-persona-list")
export class PersonasList extends Table<Persona> {
    protected override searchEnabled = true;

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    @property({ type: String })
    public override order = "expires";

    public override label = msg("Personas");
    protected override emptyStateMessage = msg("No Personas created.");

    async apiEndpoint(): Promise<PaginatedResponse<Persona>> {
        let { currentUser } = this;

        if (!currentUser) {
            const session = await this.refreshSession();
            currentUser = session ? session.user : null;
        }

        return aki(PamApi).pamPersonasList({
            ...(await this.defaultEndpointConfig()),
            // The user might have access to other tokens that aren't for their user
            // but only show tokens for their user here
            // parent: currentUser?.username,
        });
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Identifier"), "identifier"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    protected override rowLabel(item: Persona): string | null {
        return item.uuid;
    }

    renderExpanded(item: Persona): TemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("User")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${item.parent?.username}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Expiring")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-status-label ?good=${item.expiring}></ak-status-label>
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Expiring")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${item.expiring
                            ? html`<pf-tooltip
                                  position="top"
                                  .content=${item.expires?.toLocaleString()}
                              >
                                  ${formatElapsedTime(item.expires!)}
                              </pf-tooltip>`
                            : msg("-")}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Persona(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Persona) => [{ key: msg("Identifier"), value: item.uuid }]}
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

    row(item: Persona): SlottedTemplateResult[] {
        return [html`<span class="pf-m-monospace">${item.username}</span>`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-persona-list": PersonasList;
    }
}
