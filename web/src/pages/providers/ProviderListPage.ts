import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/Dropdown";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import "./ldap/LDAPProviderForm";
import "./oauth2/OAuth2ProviderForm";
import "./proxy/ProxyProviderForm";
import "./saml/SAMLProviderForm";
import "./saml/SAMLProviderImportForm";
import { TableColumn } from "../../elements/table/Table";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { Provider, ProvidersApi } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-provider-list")
export class ProviderListPage extends TablePage<Provider> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Providers`;
    }
    pageDescription(): string {
        return t`Provide support for protocols like SAML and OAuth to assigned applications.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    checkbox = true;

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Application`),
            new TableColumn(t`Type`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Provider(s)`}
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Provider): TemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.pk}"> ${item.name} </a>`,
            item.assignedApplicationName
                ? html`<i class="pf-icon pf-icon-ok pf-m-success"></i>
                      ${t`Assigned to application `}
                      <a href="#/core/applications/${item.assignedApplicationSlug}"
                          >${item.assignedApplicationName}</a
                      >`
                : html`<i class="pf-icon pf-icon-warning-triangle pf-m-warning"></i>
                      ${t`Warning: Provider not assigned to any application.`}`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update ${item.verboseName}`} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.pk,
                    }}
                    type=${ifDefined(item.component)}
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html` <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(
                        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((types) => {
                            return types.map((type) => {
                                return html`<li>
                                    <ak-forms-modal>
                                        <span slot="submit"> ${t`Create`} </span>
                                        <span slot="header"> ${t`Create ${type.name}`} </span>
                                        <ak-proxy-form slot="form" type=${type.component}>
                                        </ak-proxy-form>
                                        <button slot="trigger" class="pf-c-dropdown__menu-item">
                                            ${type.name}<br />
                                            <small>${type.description}</small>
                                        </button>
                                    </ak-forms-modal>
                                </li>`;
                            });
                        }),
                        html`<ak-spinner></ak-spinner>`,
                    )}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }
}
