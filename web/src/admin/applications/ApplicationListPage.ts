import "@goauthentik/admin/applications/ApplicationForm";
import { PFSize } from "@goauthentik/app/elements/Spinner";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/components/ak-app-icon";
import MDApplication from "@goauthentik/docs/core/applications.md";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { getURLParam } from "@goauthentik/elements/router/RouteMatch";
// import { getURLParam } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Application, CoreApi } from "@goauthentik/api";

import "./ApplicationWizardHint";

@customElement("ak-application-list")
export class ApplicationListPage extends TablePage<Application> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Applications");
    }
    pageDescription(): string {
        return msg(
            "External applications that use authentik as an identity provider via protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-applications";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            superuserFullList: true,
        });
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFCard,
            css`
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
            `,
        );
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

    renderSectionBefore(): TemplateResult {
        return html`<ak-application-wizard-hint></ak-application-wizard-hint>`;
    }

    renderSidebarAfter(): TemplateResult {
        // Rendering the wizard with .open here, as if we set the attribute in
        // renderObjectCreate() it'll open two wizards, since that function gets called twice

        /* Re-enable the wizard later:
          <ak-application-wizard
                .open=${getURLParam("createWizard", false)}
                .showButton=${false}
                ></ak-application-wizard>*/

        return html` <div class="pf-c-sidebar__panel pf-m-width-25">
            <div class="pf-c-card">
                <div class="pf-c-card__body">
                    <ak-markdown .md=${MDApplication}></ak-markdown>
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
            html`<ak-app-icon size=${PFSize.Medium} .app=${item}></ak-app-icon>`,
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
        return html`<ak-forms-modal .open=${getURLParam("createForm", false)}>
            <span slot="submit"> ${msg("Create")} </span>
            <span slot="header"> ${msg("Create Application")} </span>
            <ak-application-form slot="form"> </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }
}
