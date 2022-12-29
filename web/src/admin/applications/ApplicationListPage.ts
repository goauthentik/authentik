import "@goauthentik/admin/applications/ApplicationForm";
import "@goauthentik/admin/applications/wizard/ApplicationWizard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import MDApplication from "@goauthentik/docs/core/applications.md";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { getURLParam } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Application, CoreApi } from "@goauthentik/api";

@customElement("ak-application-list")
export class ApplicationListPage extends TablePage<Application> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Applications`;
    }
    pageDescription(): string {
        return t`External Applications which use authentik as Identity-Provider, utilizing protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.`;
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
            PFAvatar,
            PFCard,
            AKGlobal,
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
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Group`, "group"),
            new TableColumn(t`Provider`),
            new TableColumn(t`Provider Type`),
            new TableColumn(t`Actions`),
        ];
    }

    renderSidebarAfter(): TemplateResult {
        // Rendering the wizard with .open here, as if we set the attribute in
        // renderObjectCreate() it'll open two wizards, since that function gets called twice
        return html`<ak-application-wizard
                .open=${getURLParam("createWizard", false)}
                .showButton=${false}
            ></ak-application-wizard>
            <div class="pf-c-sidebar__panel pf-m-width-25">
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${t`About applications`}</div>
                    <div class="pf-c-card__body">
                        <ak-markdown .md=${MDApplication}></ak-markdown>
                    </div>
                </div>
            </div>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Application(s)`}
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderIcon(item: Application): TemplateResult {
        if (item?.metaIcon) {
            if (item.metaIcon.startsWith("fa://")) {
                const icon = item.metaIcon.replaceAll("fa://", "");
                return html`<i class="fas ${icon}"></i>`;
            }
            return html`<img
                class="app-icon pf-c-avatar"
                src="${ifDefined(item.metaIcon)}"
                alt="${t`Application Icon`}"
            />`;
        }
        return html`<i class="fas fa-share-square"></i>`;
    }

    row(item: Application): TemplateResult[] {
        return [
            this.renderIcon(item),
            html`<a href="#/core/applications/${item.slug}">
                <div>${item.name}</div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : html``}
            </a>`,
            html`${item.group || t`-`}`,
            item.provider
                ? html`<a href="#/core/providers/${item.providerObj?.pk}">
                      ${item.providerObj?.name}
                  </a>`
                : html`-`,
            html`${item.providerObj?.verboseName || t`-`}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Application`} </span>
                    <ak-application-form slot="form" .instancePk=${item.slug}>
                    </ak-application-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                ${item.launchUrl
                    ? html`<a href=${item.launchUrl} target="_blank" class="pf-c-button pf-m-plain">
                          <i class="fas fa-share-square"></i>
                      </a>`
                    : html``}`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-forms-modal .open=${getURLParam("createForm", false)}>
            <span slot="submit"> ${t`Create`} </span>
            <span slot="header"> ${t`Create Application`} </span>
            <ak-application-form slot="form"> </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
        </ak-forms-modal>`;
    }
}
