import "@goauthentik/admin/sources/SourceWizard";
import "@goauthentik/admin/sources/ldap/LDAPSourceForm";
import "@goauthentik/admin/sources/oauth/OAuthSourceForm";
import "@goauthentik/admin/sources/plex/PlexSourceForm";
import "@goauthentik/admin/sources/saml/SAMLSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

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

    async apiEndpoint(page: number): Promise<PaginatedResponse<Source>> {
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
                ${item.enabled
                    ? html``
                    : html`<ak-label color=${PFColor.Orange} ?compact=${true}>
                          ${t`Disabled`}</ak-label
                      >`}
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
            html`<div>
                <div>${item.name}</div>
                <ak-label color=${PFColor.Grey} ?compact=${true}> ${t`Built-in`}</ak-label>
            </div>`,
            html`${t`Built-in`}`,
            html``,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-source-wizard> </ak-source-wizard> `;
    }
}
