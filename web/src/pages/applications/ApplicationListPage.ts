import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { Application } from "../../api/Applications";
import { PBResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";

@customElement("ak-application-list")
export class ApplicationList extends TablePage<Application> {
    pageTitle(): string {
        return gettext("Applications");
    }
    pageDescription(): string {
        return gettext("External Applications which use authentik as Identity-Provider, utilizing protocols like OAuth2 and SAML.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-applications");
    }

    apiEndpoint(page: number): Promise<PBResponse<Application>> {
        return Application.list({
            ordering: this.order || "order",
            page: page,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Slug", "slug"),
            new TableColumn("Provider"),
            new TableColumn("Provider Type"),
            new TableColumn(""),
        ];
    }

    row(item: Application): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.slug}`,
            html`${item.provider}`,
            html`${item.provider}`,
            html`
            <ak-modal-button href="administration/policies/bindings/${item.pk}/update/">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="administration/policies/bindings/${item.pk}/delete/">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }
}
