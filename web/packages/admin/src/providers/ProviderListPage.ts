import "@goauthentik/admin/applications/ApplicationWizardHint.js";
import "@goauthentik/admin/providers/ProviderWizard.js";
import "@goauthentik/admin/providers/ldap/LDAPProviderForm.js";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm.js";
import "@goauthentik/admin/providers/proxy/ProxyProviderForm.js";
import "@goauthentik/admin/providers/rac/RACProviderForm.js";
import "@goauthentik/admin/providers/radius/RadiusProviderForm.js";
import "@goauthentik/admin/providers/saml/SAMLProviderForm.js";
import "@goauthentik/admin/providers/scim/SCIMProviderForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { uiConfig } from "@goauthentik/common/ui/config.js";
import "@goauthentik/elements/buttons/SpinnerButton/ak-spinner-button.js";
import "@goauthentik/elements/forms/DeleteBulkForm.js";
import "@goauthentik/elements/forms/ModalForm.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import { PaginatedResponse } from "@goauthentik/elements/table/Table.js";
import { TableColumn } from "@goauthentik/elements/table/Table.js";
import { TablePage } from "@goauthentik/elements/table/TablePage.js";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Provider, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-list")
export class ProviderListPage extends TablePage<Provider> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Providers");
    }
    pageDescription(): string {
        return msg("Provide support for protocols like SAML and OAuth to assigned applications.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Application")),
            new TableColumn(msg("Type")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Provider(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Provider) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersAllUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: Provider) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersAllDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    rowApp(item: Provider): TemplateResult {
        if (item.assignedApplicationName) {
            return html`<i class="pf-icon pf-icon-ok pf-m-success"></i>
                ${msg("Assigned to application ")}
                <a href="#/core/applications/${item.assignedApplicationSlug}"
                    >${item.assignedApplicationName}</a
                >`;
        }
        if (item.assignedBackchannelApplicationName) {
            return html`<i class="pf-icon pf-icon-ok pf-m-success"></i>
                ${msg("Assigned to application (backchannel) ")}
                <a href="#/core/applications/${item.assignedBackchannelApplicationSlug}"
                    >${item.assignedBackchannelApplicationName}</a
                >`;
        }
        return html`<i class="pf-icon pf-icon-warning-triangle pf-m-warning"></i> ${msg(
                "Warning: Provider not assigned to any application.",
            )}`;
    }

    row(item: Provider): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.pk}"> ${item.name} </a>`,
            this.rowApp(item),
            html`${item.verboseName}`,
            html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg(str`Update ${item.verboseName}`)} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.pk,
                    }}
                    type=${item.component}
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-provider-wizard> </ak-provider-wizard> `;
    }
}
