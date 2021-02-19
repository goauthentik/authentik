import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { AKResponse } from "../../api/Client";
import { OutpostServiceConnection } from "../../api/Outposts";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";

import "./OutpostHealth";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import { until } from "lit-html/directives/until";

@customElement("ak-outpost-service-connection-list")
export class OutpostServiceConnectionListPage extends TablePage<OutpostServiceConnection> {
    pageTitle(): string {
        return "Outpost Service-Connections";
    }
    pageDescription(): string | undefined {
        return "Outpost Service-Connections define how authentik connects to external platforms to manage and deploy Outposts.";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }
    searchEnabled(): boolean {
        return true;
    }

    apiEndpoint(page: number): Promise<AKResponse<OutpostServiceConnection>> {
        return OutpostServiceConnection.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }
    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Type"),
            new TableColumn("Local", "local"),
            new TableColumn("State"),
            new TableColumn(""),
        ];
    }

    @property()
    order = "name";

    row(item: OutpostServiceConnection): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.verbose_name}`,
            html`${item.local ? "Yes" : "No"}`,
            html`${until(OutpostServiceConnection.state(item.pk).then((state) => {
                if (state.healthy) {
                    return html`<i class="fas fa-check pf-m-success"></i> ${state.version}`;
                }
                return html`<i class="fas fa-times pf-m-danger"></i> ${gettext("Unhealthy")}`;
            }), html`<ak-spinner></ak-spinner>`)}`,
            html`
            <ak-modal-button href="${OutpostServiceConnection.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${OutpostServiceConnection.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${gettext("Create")}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(OutpostServiceConnection.getTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-modal-button href="${type.link}">
                                <button slot="trigger" class="pf-c-dropdown__menu-item">${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                                <div slot="modal"></div>
                            </ak-modal-button>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

}
