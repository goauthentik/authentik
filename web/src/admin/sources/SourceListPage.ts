import "#admin/sources/SourceWizard";
import "#admin/sources/kerberos/KerberosSourceForm";
import "#admin/sources/ldap/LDAPSourceForm";
import "#admin/sources/oauth/OAuthSourceForm";
import "#admin/sources/plex/PlexSourceForm";
import "#admin/sources/saml/SAMLSourceForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CustomFormElementTagName } from "#elements/forms/unsafe";
import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { Source, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-list")
export class SourceListPage extends TablePage<Source> {
    public pageTitle = msg("Federation and Social login");
    public pageDescription = msg(
        "Sources of identities, which can either be synced into authentik's database, or can be used by users to authenticate and enroll themselves.",
    );
    public pageIcon = "pf-icon pf-icon-middleware";
    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Source>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesAllList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Type")],
        ["", null, msg("Row Actions")],
    ];

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

    row(item: Source): SlottedTemplateResult[] {
        if (item.component === "") {
            return this.rowInbuilt(item);
        }
        return [
            html`<a href="#/core/sources/${item.slug}">
                <div>${item.name}</div>
                ${item.enabled
                    ? nothing
                    : html`<ak-label color=${PFColor.Orange} compact>
                          ${msg("Disabled")}</ak-label
                      >`}
            </a>`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                ${StrictUnsafe<CustomFormElementTagName>(item.component, {
                    slot: "form",
                    instancePk: item.slug,
                })}
                <span slot="submit">${msg("Update")}</span>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    rowInbuilt(item: Source): SlottedTemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                <ak-label color=${PFColor.Grey} compact> ${msg("Built-in")}</ak-label>
            </div>`,
            html`${msg("Built-in")}`,
            nothing,
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
