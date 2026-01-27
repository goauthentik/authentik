import "#elements/forms/ConfirmationForm";
import "#admin/applications/ApplicationForm";
import "#elements/AppIcon";
import "#elements/ak-mdx/ak-mdx";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "./ApplicationWizardHint.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { WithBrandConfig } from "#elements/mixins/branding";
import { getURLParam } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Application, CoreApi, PoliciesApi } from "@goauthentik/api";

import MDApplication from "~docs/add-secure-apps/applications/index.md";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

export const applicationListStyle = css`
    /* Fix alignment issues with images in tables */
    .pf-c-table tbody > tr > * {
        vertical-align: middle;
    }
    tr td:first-child {
        width: auto;
        min-width: 0px;
        text-align: center;
        vertical-align: middle;
    }
    .pf-c-sidebar.pf-m-gutter > .pf-c-sidebar__main > * + * {
        margin-left: calc(var(--pf-c-sidebar__main--child--MarginLeft) / 2);
    }
`;

@customElement("ak-application-list")
export class ApplicationListPage extends WithBrandConfig(TablePage<Application>) {
    protected override searchEnabled = true;
    public pageTitle = msg("Applications");
    public get pageDescription() {
        return msg(
            str`External applications that use ${this.brandingTitle} as an identity provider via protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.`,
        );
    }
    public pageIcon = "pf-icon pf-icon-applications";

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ...(await this.defaultEndpointConfig()),
            superuserFullList: true,
        });
    }

    static styles: CSSResult[] = [...TablePage.styles, PFCard, applicationListStyle];

    protected columns: TableColumn[] = [
        ["", undefined, msg("Application Icon")],
        [msg("Name"), "name"],
        [msg("Group"), "group"],
        [msg("Provider")],
        [msg("Provider Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected renderSidebarAfter(): TemplateResult {
        return html`<aside
            aria-label=${msg("Applications Documentation")}
            class="pf-c-sidebar__panel"
        >
            <div class="pf-c-card">
                <div class="pf-c-card__body">
                    <ak-mdx .url=${MDApplication}></ak-mdx>
                </div>
            </div>
        </aside>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Application(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Application) => {
                return new CoreApi(DEFAULT_CONFIG).coreApplicationsUsedByList({
                    slug: item.slug,
                });
            }}
            .delete=${(item: Application) => {
                return new CoreApi(DEFAULT_CONFIG).coreApplicationsDestroy({
                    slug: item.slug,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Application): SlottedTemplateResult[] {
        return [
            html`<ak-app-icon
                aria-label=${msg(str`Application icon for "${item.name}"`)}
                name=${item.name}
                icon=${ifPresent(item.metaIconUrl)}
                .iconThemedUrls=${item.metaIconThemedUrls}
            ></ak-app-icon>`,
            html`<a href="#/core/applications/${item.slug}">
                <div>${item.name}</div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : nothing}
            </a>`,
            item.group ? html`${item.group}` : html`<span aria-label="None">${msg("-")}</span>`,
            item.provider
                ? html`<a href="#/core/providers/${item.providerObj?.pk}">
                      ${item.providerObj?.name}
                  </a>`
                : html`-`,
            html`${item.providerObj?.verboseName || msg("-")}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Application")}</span>
                    <ak-application-form slot="form" .instancePk=${item.slug}>
                    </ak-application-form>
                    <button
                        slot="trigger"
                        class="pf-c-button pf-m-plain"
                        aria-label=${msg(str`Edit "${item.name}"`)}
                    >
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                ${item.launchUrl
                    ? html`<a
                          href=${item.launchUrl}
                          target="_blank"
                          class="pf-c-button pf-m-plain"
                          aria-label=${msg(str`Open "${item.name}"`)}
                      >
                          <pf-tooltip position="top" content=${msg("Open")}>
                              <i class="fas fa-share-square" aria-hidden="true"></i>
                          </pf-tooltip>
                      </a>`
                    : nothing}
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html` <ak-application-wizard .open=${getURLParam("createWizard", false)}>
                <button
                    slot="trigger"
                    class="pf-c-button pf-m-primary"
                    data-ouia-component-id="start-application-wizard"
                >
                    ${msg("Create with Provider")}
                </button>
            </ak-application-wizard>
            <ak-forms-modal .open=${getURLParam("createForm", false)}>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Application")}</span>
                <ak-application-form slot="form"> </ak-application-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>`;
    }

    renderToolbar(): TemplateResult {
        return html` ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared application cache")}
                errorMessage=${msg("Failed to delete application cache")}
                action=${msg("Clear cache")}
                .onConfirm=${() => {
                    return new PoliciesApi(DEFAULT_CONFIG).policiesAllCacheClearCreate();
                }}
            >
                <span slot="header">${msg("Clear Application cache")}</span>
                <p slot="body">
                    ${msg(
                        "Are you sure you want to clear the application cache? This will cause all policies to be re-evaluated on their next usage.",
                    )}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${msg("Clear cache")}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-list": ApplicationListPage;
    }
}
