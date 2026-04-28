import "#admin/providers/ak-provider-wizard";
import "#admin/providers/google_workspace/GoogleWorkspaceProviderForm";
import "#admin/providers/ldap/LDAPProviderForm";
import "#admin/providers/microsoft_entra/MicrosoftEntraProviderForm";
import "#admin/providers/oauth2/OAuth2ProviderForm";
import "#admin/providers/proxy/ProxyProviderForm";
import "#admin/providers/rac/RACProviderForm";
import "#admin/providers/radius/RadiusProviderForm";
import "#admin/providers/saml/SAMLProviderForm";
import "#admin/providers/scim/SCIMProviderForm";
import "#admin/providers/ssf/SSFProviderFormPage";
import "#admin/providers/wsfed/WSFederationProviderForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButtonByTagName } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AKProviderWizard } from "#admin/providers/ak-provider-wizard";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-list")
export class ProviderListPage extends TablePage<Provider> {
    protected override searchEnabled = true;

    override pageTitle = msg("Providers");

    public pageDescription = msg(
        "Provide support for protocols like SAML and OAuth to assigned applications.",
    );

    public pageIcon = "pf-icon pf-icon-integration";

    override checkbox = true;
    override clearOnRefresh = true;

    @property()
    public order = "name";

    public searchLabel = msg("Provider Search");
    public searchPlaceholder = msg("Search for provider by name, type or assigned application...");

    override async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Application")],
        [msg("Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Provider(s)")}
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

    #rowApp(item: Provider): TemplateResult {
        if (item.assignedApplicationName) {
            return html`<i class="pf-icon pf-icon-ok pf-m-success" aria-hidden="true"></i>
                ${msg("Assigned to application ")}
                <a href="#/core/applications/${item.assignedApplicationSlug}"
                    >${item.assignedApplicationName}</a
                >`;
        }

        if (item.assignedBackchannelApplicationName) {
            return html`<i class="pf-icon pf-icon-ok pf-m-success" aria-hidden="true"></i>
                ${msg("Assigned to application (backchannel) ")}
                <a href="#/core/applications/${item.assignedBackchannelApplicationSlug}"
                    >${item.assignedBackchannelApplicationName}</a
                >`;
        }

        return html`<i aria-hidden="true" class="pf-icon pf-icon-warning-triangle pf-m-warning"></i
            ><span>${msg("Provider not assigned to any application.")}</span>`;
    }

    override row(item: Provider): SlottedTemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.pk}">${item.name}</a>`,
            this.#rowApp(item),
            item.verboseName,
            html`<div class="ak-c-table__actions">
                ${IconEditButtonByTagName(item.component, item.pk)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`
            <button
                class="pf-c-button pf-m-primary"
                type="button"
                aria-description="${msg("Open the wizard to create a new provider.")}"
                ${AKProviderWizard.asModalInvoker()}
            >
                ${msg("New Provider")}
            </button>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-list": ProviderListPage;
    }
}
