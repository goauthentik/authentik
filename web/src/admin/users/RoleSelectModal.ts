import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TableModal } from "#elements/table/TableModal";
import { SlottedTemplateResult } from "#elements/types";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-user-role-select-table")
export class RoleSelectModal extends TableModal<Role> {
    static styles: CSSResult[] = [...super.styles, PFBanner];

    checkbox = true;
    checkboxChip = true;

    protected override searchEnabled = true;
    public supportsQL = true;

    @property({ attribute: false })
    public confirm: ((selectedItems: Role[]) => Promise<unknown>) | null = null;

    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Role>> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns: TableColumn[] = [[msg("Name"), "name"]];

    row(item: Role): SlottedTemplateResult[] {
        return [html`<div>${item.name}</div>`];
    }

    renderSelectedChip(item: Role): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): SlottedTemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        ${msg("Select roles to attach to the user")}
                    </h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        if (!this.confirm) {
                            return;
                        }
                        return this.confirm(this.selectedElements).then(() => {
                            this.open = false;
                        });
                    }}
                    class="pf-m-primary"
                >
                    ${msg("Add")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-role-select-table": RoleSelectModal;
    }
}
