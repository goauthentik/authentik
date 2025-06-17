import "@goauthentik/admin/applications/ApplicationWizardHint";
import "@goauthentik/admin/providers/ProviderWizard";
import "@goauthentik/admin/providers/google_workspace/GoogleWorkspaceProviderForm";
import "@goauthentik/admin/providers/ldap/LDAPProviderForm";
import "@goauthentik/admin/providers/microsoft_entra/MicrosoftEntraProviderForm";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import "@goauthentik/admin/providers/proxy/ProxyProviderForm";
import "@goauthentik/admin/providers/rac/RACProviderForm";
import "@goauthentik/admin/providers/radius/RadiusProviderForm";
import "@goauthentik/admin/providers/saml/SAMLProviderForm";
import "@goauthentik/admin/providers/scim/SCIMProviderForm";
import "@goauthentik/admin/providers/ssf/SSFProviderFormPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Provider, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-list")
export class ProviderListPage extends TablePage<Provider> {
    override searchEnabled(): boolean {
        return true;
    }

    override pageTitle(): string {
        return msg("Providers");
    }

    override pageDescription(): string {
        return msg("Provide support for protocols like SAML and OAuth to assigned applications.");
    }

    override pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    override checkbox = true;
    override clearOnRefresh = true;

    @property()
    public order = "name";

    public searchLabel = msg("Provider name");
    public searchPlaceholder = msg("Search for providers…");

    override async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList(
            await this.defaultEndpointConfig(),
        );
    }

    override columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Application")),
            new TableColumn(msg("Type")),
            new TableColumn(msg("Actions")),
        ];
    }

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

        return html`<i aria-hidden="true" class="pf-icon pf-icon-warning-triangle pf-m-warning"></i>
            ${msg("Warning: Provider not assigned to any application.")}`;
    }

    override row(item: Provider): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.pk}"> ${item.name} </a>`,
            this.#rowApp(item),
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
                <button
                    aria-label=${msg("Edit provider")}
                    slot="trigger"
                    class="pf-c-button pf-m-plain"
                >
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i aria-hidden="true" class="fas fa-edit"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
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
