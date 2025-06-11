import "#admin/applications/ApplicationForm";
import { DEFAULT_CONFIG } from "#common/api/config";
import "#elements/AppIcon";
import "#elements/ak-mdx/ak-mdx";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { WithBrandConfig } from "#elements/mixins/branding";
import { getURLParam } from "#elements/router/RouteMatch";
import { PaginatedResponse } from "#elements/table/Table";
import { TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import MDApplication from "~docs/add-secure-apps/applications/index.md";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Application, CoreApi, PoliciesApi } from "@goauthentik/api";

import "./ApplicationWizardHint.js";

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
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Applications");
    }
    pageDescription(): string {
        return msg(
            str`External applications that use ${this.brandingTitle} as an identity provider via protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.`,
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-applications";
    }

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

    static get styles(): CSSResult[] {
        return TablePage.styles.concat(PFCard, applicationListStyle);
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(""),
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Group"), "group"),
            new TableColumn(msg("Provider")),
            new TableColumn(msg("Provider Type")),
            new TableColumn(msg("Actions")),
        ];
    }

    protected renderSidebarAfter(): TemplateResult {
        return html`<div class="pf-c-sidebar__panel pf-m-width-25">
            <div class="pf-c-card">
                <div class="pf-c-card__body">
                    <ak-mdx .url=${MDApplication}></ak-mdx>
                </div>
            </div>
        </div>`;
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

    row(item: Application): TemplateResult[] {
        return [
            html`<ak-app-icon
                name=${item.name}
                icon=${ifDefined(item.metaIcon || undefined)}
            ></ak-app-icon>`,
            html`<a href="#/core/applications/${item.slug}">
                <div>${item.name}</div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : html``}
            </a>`,
            html`${item.group || msg("-")}`,
            item.provider
                ? html`<a href="#/core/providers/${item.providerObj?.pk}">
                      ${item.providerObj?.name}
                  </a>`
                : html`-`,
            html`${item.providerObj?.verboseName || msg("-")}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Application")} </span>
                    <ak-application-form slot="form" .instancePk=${item.slug}>
                    </ak-application-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                ${item.launchUrl
                    ? html`<a href=${item.launchUrl} target="_blank" class="pf-c-button pf-m-plain">
                          <pf-tooltip position="top" content=${msg("Open")}>
                              <i class="fas fa-share-square"></i>
                          </pf-tooltip>
                      </a>`
                    : html``}`,
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
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Application")} </span>
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
                <span slot="header"> ${msg("Clear Application cache")} </span>
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
