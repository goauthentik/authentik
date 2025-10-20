import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TableModal } from "#elements/table/TableModal";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-user-group-select-table")
export class GroupSelectModal extends TableModal<Group> {
    checkbox = true;
    checkboxChip = true;

    protected override searchEnabled = true;
    public supportsQL = true;

    @property()
    confirm!: (selectedItems: Group[]) => Promise<unknown>;

    order = "name";

    static styles: CSSResult[] = [...super.styles, PFBanner];

    async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Superuser"), "is_superuser"],
        [msg("Members"), ""],
    ];

    row(item: Group): SlottedTemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html` <ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html`${(item.users || []).length}`,
        ];
    }

    renderSelectedChip(item: Group): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): SlottedTemplateResult {
        const willSuperuser = this.selectedElements.filter((g) => g.isSuperuser).length > 0;
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Select groups to add user to")}</h1>
                </div>
            </section>
            ${willSuperuser
                ? html`
                      <div class="pf-c-banner pf-m-warning">
                          ${msg(
                              "Warning: Adding the user to the selected group(s) will give them superuser permissions.",
                          )}
                      </div>
                  `
                : nothing}
            <section class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
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
        "ak-user-group-select-table": GroupSelectModal;
    }
}
