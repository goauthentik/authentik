import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import "@goauthentik/web/elements/forms/DeleteBulkForm";
import "@goauthentik/web/elements/forms/ModalForm";
import "@goauthentik/web/elements/forms/ProxyForm";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TablePage } from "@goauthentik/web/elements/table/TablePage";
import "@goauthentik/web/pages/sources/SourceWizard";
import "@goauthentik/web/pages/sources/ldap/LDAPSourceForm";
import "@goauthentik/web/pages/sources/oauth/OAuthSourceForm";
import "@goauthentik/web/pages/sources/plex/PlexSourceForm";
import "@goauthentik/web/pages/sources/saml/SAMLSourceForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Source, SourcesApi } from "@goauthentik/api";

@customElement("ak-source-list")
export class SourceListPage extends TablePage<Source> {
    pageTitle(): string {
        return t`Federation & Social login`;
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

    renderObjectCreate(): TemplateResult {
        return html`<ak-source-wizard> </ak-source-wizard> `;
    }
}
