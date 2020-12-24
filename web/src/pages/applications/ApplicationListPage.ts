import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { Application } from "../../api/Applications";
import { PBResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";

@customElement("ak-application-list")
export class ApplicationList extends TablePage<Application> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Applications");
    }
    pageDescription(): string {
        return gettext("External Applications which use authentik as Identity-Provider, utilizing protocols like OAuth2 and SAML.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-applications");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<PBResponse<Application>> {
        return Application.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(""),
            new TableColumn("Name", "name"),
            new TableColumn("Slug", "slug"),
            new TableColumn("Provider"),
            new TableColumn("Provider Type"),
            new TableColumn(""),
        ];
    }

    row(item: Application): TemplateResult[] {
        return [
            html`
            ${item.meta_icon ?
        html`<img class="app-icon pf-c-avatar" src="${item.meta_icon}" alt="${gettext("Application Icon")}">` :
        html`<i class="pf-icon pf-icon-arrow"></i>`}`,
            html`<a href="#/applications/${item.slug}/">
                <div>
                    ${item.name}
                </div>
                ${item.meta_publisher ? html`<small>${item.meta_publisher}</small>` : html``}
            </a>`,
            html`<code>${item.slug}</code>`,
            html`${item.provider.name}`,
            html`${item.provider.verbose_name}`,
            html`
            <ak-modal-button href="${Application.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Application.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${Application.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
