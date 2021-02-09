import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Source } from "../../api/Sources";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";

@customElement("ak-source-list")
export class SourceListPage extends TablePage<Source> {
    pageTitle(): string {
        return "Sources";
    }
    pageDescription(): string | undefined {
        return "External Sources which can be used to get Identities into authentik, for example Social Providers like Twiter and GitHub or Enterprise Providers like ADFS and LDAP.";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-middleware";
    }
    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Source>> {
        return Source.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Type", "verbose_name"),
            new TableColumn(""),
        ];
    }

    row(item: Source): TemplateResult[] {
        return [
            html`<a href="#/sources/${item.slug}">
                <div>${item.name}</div>
                ${item.enabled ? html`` : html`<small>${gettext("Disabled")}</small>`}
            </a>`,
            html`${item.verbose_name}`,
            html`
            <ak-modal-button href="${Source.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>&nbsp;
            <ak-modal-button href="${Source.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

}
