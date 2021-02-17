import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { Provider } from "../../api/Providers";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/Dropdown";
import { TableColumn } from "../../elements/table/Table";
import { until } from "lit-html/directives/until";

@customElement("ak-provider-list")
export class ProviderListPage extends TablePage<Provider> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Provider");
    }
    pageDescription(): string {
        return gettext("Provide support for protocols like SAML and OAuth to assigned applications.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-integration");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Provider>> {
        return Provider.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Application"),
            new TableColumn("Type", "type"),
            new TableColumn(""),
        ];
    }

    row(item: Provider): TemplateResult[] {
        return [
            html`<a href="#/providers/${item.pk}">
                ${item.name}
            </a>`,
            item.assigned_application_name ?
                html`<i class="pf-icon pf-icon-ok"></i>
                    ${gettext("Assigned to application ")}
                    <a href="#/applications/${item.assigned_application_slug}">${item.assigned_application_name}</a>` :
                html`<i class="pf-icon pf-icon-warning-triangle"></i>
                ${gettext("Warning: Provider not assigned to any application.")}`,
            html`${item.verbose_name}`,
            html`
            <ak-modal-button href="${Provider.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Provider.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
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
                ${until(Provider.getTypes().then((types) => {
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
