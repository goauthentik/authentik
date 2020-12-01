import { gettext } from "django";
import { customElement } from "lit-element";
import { Application } from "../../api/application";
import { PBResponse } from "../../api/client";
import { TablePage } from "../../elements/table/TablePage";

@customElement("pb-application-list")
export class ApplicationList extends TablePage<Application> {
    pageTitle(): string {
        return gettext("Applications");
    }
    pageDescription(): string {
        return gettext("External Applications which use passbook as Identity-Provider, utilizing protocols like OAuth2 and SAML.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-applications");
    }

    apiEndpoint(page: number): Promise<PBResponse<Application>> {
        return Application.list({
            ordering: "order",
            page: page,
        });
    }

    columns(): string[] {
        return ["Name", "Slug", "Provider", "Provider Type", ""];
    }

    row(item: Application): string[] {
        return [
            item.name,
            item.slug,
            item.provider.toString(),
            item.provider.toString(),
            `
            <pb-modal-button href="administration/policies/bindings/${item.pk}/update/">
                <pb-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </pb-spinner-button>
                <div slot="modal"></div>
            </pb-modal-button>
            <pb-modal-button href="administration/policies/bindings/${item.pk}/delete/">
                <pb-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </pb-spinner-button>
                <div slot="modal"></div>
            </pb-modal-button>
            `,
        ];
    }
}
