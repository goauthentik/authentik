import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { Source, SourcesApi } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import "./ldap/LDAPSourceForm";
import "./oauth/OAuthSourceForm";
import "./plex/PlexSourceForm";
import "./saml/SAMLSourceForm";

@customElement("ak-source-list")
export class SourceListPage extends TablePage<Source> {
    pageTitle(): string {
        return t`Sources`;
    }
    pageDescription(): string | undefined {
        return t`Sources of identities, which can either be synced into authentik's database, or can be used by users to authenticate and enroll themselves.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-middleware";
    }
    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<AKResponse<Source>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(t`Name`, "name"), new TableColumn(t`Type`), new TableColumn("")];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Source(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Source) => {
                return new SourcesApi(DEFAULT_CONFIG).sourcesAllUsedByList({
                    slug: item.slug,
                });
            }}
            .delete=${(item: Source) => {
                return new SourcesApi(DEFAULT_CONFIG).sourcesAllDestroy({
                    slug: item.slug,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Source): TemplateResult[] {
        if (item.component === "") {
            return this.rowInbuilt(item);
        }
        return [
            html`<a href="#/core/sources/${item.slug}">
                <div>${item.name}</div>
                ${item.enabled ? html`` : html`<small>${t`Disabled`}</small>`}
            </a>`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update ${item.verboseName}`} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.slug,
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

    rowInbuilt(item: Source): TemplateResult[] {
        return [
            html`<span>
                <div>${item.name}</div>
                <small>${t`Built-in`}</small>
            </span>`,
            html`${t`Built-in`}`,
            html``,
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
                        new SourcesApi(DEFAULT_CONFIG).sourcesAllTypesList().then((types) => {
                            return types.map((type) => {
                                return html`<li>
                                    <ak-forms-modal>
                                        <span slot="submit"> ${t`Create`} </span>
                                        <span slot="header"> ${t`Create ${type.name}`} </span>
                                        <ak-proxy-form
                                            slot="form"
                                            .args=${{
                                                modelName: type.modelName,
                                            }}
                                            type=${type.component}
                                        >
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
