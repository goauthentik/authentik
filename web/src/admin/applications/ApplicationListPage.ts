import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/forms/ConfirmationForm";
import "#elements/AppIcon";
import "#elements/ak-mdx/ak-mdx";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/dialogs/ak-modal";
import "#admin/applications/ApplicationForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton } from "#elements/dialogs";
import { WithBrandConfig } from "#elements/mixins/branding";
import { getURLParam } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { ApplicationForm } from "#admin/applications/ApplicationForm";
import Styles from "#admin/applications/ApplicationListPage.css";
import { AKApplicationWizard } from "#admin/applications/wizard/ak-application-wizard";

import { Application, CoreApi, PoliciesApi } from "@goauthentik/api";

import MDApplication from "~docs/add-secure-apps/applications/index.md";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

export const applicationListStyle = css``;

@customElement("ak-application-list")
export class ApplicationListPage extends WithBrandConfig(TablePage<Application>) {
    public static styles: CSSResult[] = [
        // ---
        ...TablePage.styles,
        PFCard,
        Styles,
    ];

    protected override searchEnabled = true;
    public pageTitle = msg("Applications");
    public searchLabel = msg("Applications search");
    public searchPlaceholder = msg("Search for application by name, group or provider...");

    public get pageDescription() {
        return msg(
            str`External applications that use ${this.brandingTitle} as an identity provider via protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.`,
        );
    }
    public pageIcon = "pf-icon pf-icon-applications";

    public override checkbox = true;
    public override clearOnRefresh = true;

    @property()
    public order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ...(await this.defaultEndpointConfig()),
            superuserFullList: true,
        });
    }

    public override firstUpdated(changed: PropertyValues<this>): void {
        super.firstUpdated(changed);

        if (getURLParam("createWizard", false)) {
            AKApplicationWizard.showModal();
        } else if (getURLParam("createForm", false)) {
            ApplicationForm.showModal();
        }
    }

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

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Application(s)")}
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

    protected row(item: Application): SlottedTemplateResult[] {
        return [
            html`<ak-app-icon
                aria-label=${msg(str`Application icon for "${item.name}"`)}
                role="img"
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
            html`<div class="ak-c-table__actions">
                ${IconEditButton(ApplicationForm, item.slug)}
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

    protected override renderObjectCreate(): TemplateResult {
        return html`<ak-dropdown class="pf-c-dropdown">
            <div class="pf-c-dropdown__toggle pf-m-primary pf-m-split-button pf-m-action">
                <button
                    class="pf-c-dropdown__toggle-button"
                    type="button"
                    ${AKApplicationWizard.asModalInvoker()}
                >
                    ${msg("New Application")}
                </button>

                <button
                    class="pf-c-dropdown__toggle-button"
                    type="button"
                    id="new-application-toggle"
                    aria-haspopup="menu"
                    aria-controls="new-application-menu"
                    tabindex="0"
                    aria-label=${msg("New Application options")}
                >
                    <i class="fas fa-caret-down" aria-hidden="true"></i>
                </button>
            </div>

            <menu
                class="pf-c-dropdown__menu"
                hidden
                id="new-application-menu"
                aria-labelledby="new-application-toggle"
                tabindex="-1"
            >
                <li role="presentation">
                    <button
                        type="button"
                        role="menuitem"
                        class="pf-c-dropdown__menu-item"
                        ${AKApplicationWizard.asModalInvoker()}
                        aria-description=${msg(
                            "Opens the new application wizard, which will guide you through creating a new application with an existing provider.",
                        )}
                    >
                        ${msg("with New Provider...")}
                    </button>
                </li>
                <li role="presentation">
                    <button
                        type="button"
                        role="menuitem"
                        class="pf-c-dropdown__menu-item"
                        ${ApplicationForm.asModalInvoker()}
                        aria-description=${msg(
                            "Opens the new application form, which will guide you through creating a new application with an existing provider.",
                        )}
                    >
                        ${msg("with Existing Provider...")}
                    </button>
                </li>
            </menu>
        </ak-dropdown>`;
    }

    protected override renderToolbar(): TemplateResult {
        return html`${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared application cache")}
                errorMessage=${msg("Failed to delete application cache")}
                action=${msg("Clear Cache")}
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
