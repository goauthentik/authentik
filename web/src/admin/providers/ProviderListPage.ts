import "#admin/applications/ApplicationWizardHint";
import "#admin/providers/ProviderWizard";
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
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
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
    public searchPlaceholder = msg("Search for providers…");

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
            html`${item.verboseName}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg(str`Update ${item.verboseName}`)}</span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.pk,
                        }}
                        type=${item.component}
                    >
                    </ak-proxy-form>
                    <button
                        aria-label=${msg(str`Edit "${item.name}" provider`)}
                        slot="trigger"
                        class="pf-c-button pf-m-plain"
                    >
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i aria-hidden="true" class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            </div>`,
        ];
    }

    override renderObjectCreate(): TemplateResult {
        return html`<ak-provider-wizard> </ak-provider-wizard> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-list": ProviderListPage;
    }
}
