import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TableModal } from "@goauthentik/elements/table/TableModal";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { CoreApi, Group } from "@goauthentik/api";

@customElement("ak-user-group-select-table")
export class GroupSelectModal extends TableModal<Group> {
    checkbox = true;
    checkboxChip = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: Group[]) => Promise<unknown>;

    order = "name";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFBanner);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "username"),
            new TableColumn(msg("Superuser"), "is_superuser"),
            new TableColumn(msg("Members"), ""),
        ];
    }

    row(item: Group): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html` <ak-label color=${item.isSuperuser ? PFColor.Green : PFColor.Grey}>
                ${item.isSuperuser ? msg("Yes") : msg("No")}
            </ak-label>`,
            html`${(item.users || []).length}`,
        ];
    }

    renderSelectedChip(item: Group): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): TemplateResult {
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
                : html``}
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
