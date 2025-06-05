import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "#admin/sources/SourceWizard";
import "#admin/sources/kerberos/KerberosSourceForm";
import "#admin/sources/ldap/LDAPSourceForm";
import "#admin/sources/oauth/OAuthSourceForm";
import "#admin/sources/plex/PlexSourceForm";
import "#admin/sources/saml/SAMLSourceForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import { Source, SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-list")
export class SourceListPage extends TablePage<Source> {
    pageTitle(): string {
        return msg("Federation and Social login");
    }
    pageDescription(): string | undefined {
        return msg(
            "Sources of identities, which can either be synced into authentik's database, or can be used by users to authenticate and enroll themselves.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-middleware";
    }
    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Source>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesAllList(await this.defaultEndpointConfig());
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Type")),
            new TableColumn(""),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled =
            this.selectedElements.length < 1 ||
            this.selectedElements.some((item) => item.component === "");
        const nonBuiltInSources = this.selectedElements.filter((item) => item.component !== "");
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Source(s)")}
            .objects=${nonBuiltInSources}
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
                ${msg("Delete")}
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
                          ${msg("Disabled")}</ak-label
                      >`}
            </a>`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg(str`Update ${item.verboseName}`)} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.slug,
                    }}
                    type=${ifDefined(item.component)}
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

    rowInbuilt(item: Source): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                <ak-label color=${PFColor.Grey} ?compact=${true}> ${msg("Built-in")}</ak-label>
            </div>`,
            html`${msg("Built-in")}`,
            html``,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-source-wizard> </ak-source-wizard> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-list": SourceListPage;
    }
}
