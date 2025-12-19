import "#admin/applications/ApplicationForm";
import "#elements/AppIcon";
import "#elements/ak-mdx/ak-mdx";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "./ApplicationWizardHint.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { renderDeleteBulkFormModal } from "#elements/forms/DeleteBulkForm";
import { WithBrandConfig } from "#elements/mixins/branding";
import { renderModal } from "#elements/modals/utils";
import { getURLParam } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Application, CoreApi, PoliciesApi } from "@goauthentik/api";

import MDApplication from "~docs/add-secure-apps/applications/index.md";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

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

function renderEditApplicationForm(applicationSlug: string | null): Promise<void> {
    return renderModal(
        html`<ak-forms-modal>
            <ak-application-form pk=${applicationSlug}></ak-application-form>
        </ak-forms-modal>`,
    );
}

function renderCreateApplicationForm(): Promise<void> {
    return renderModal(
        html`<ak-forms-modal>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("Create Application")}</span>
            <ak-application-form></ak-application-form>
        </ak-forms-modal>`,
    );
}
// function renderCreateApplicationForm2(): Promise<void> {
//     return FormsModal.html`<ak-application-form></ak-application-form>`
// }

@customElement("ak-application-list")
export class ApplicationListPage extends WithBrandConfig(TablePage<Application>) {
    static styles: CSSResult[] = [...TablePage.styles, PFCard, applicationListStyle];

    //#region Protected Properties

    @state()
    protected activeApplicationSlug: string | null = null;

    protected override searchEnabled = true;

    protected override async apiEndpoint(): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ...(await this.defaultEndpointConfig()),
            superuserFullList: true,
        });
    }

    protected columns: TableColumn[] = [
        ["", undefined, msg("Application Icon")],
        [msg("Name"), "name"],
        [msg("Group"), "group"],
        [msg("Provider")],
        [msg("Provider Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    //#endregion

    //#region Public Properties

    public pageTitle = msg("Applications");

    public override checkbox = true;
    public override clearOnRefresh = true;

    public get pageDescription() {
        return msg(
            str`External applications that use ${this.brandingTitle} as an identity provider via protocols like OAuth2 and SAML. All applications are shown here, even ones you cannot access.`,
        );
    }
    public pageIcon = "pf-icon pf-icon-applications";

    @property({ type: String })
    public order = "name";

    //#endregion

    //#region Lifecycle

    public override firstUpdated(): void {
        super.firstUpdated();

        const createForm = getURLParam("createForm", false);

        if (createForm) {
            renderCreateApplicationForm();
        }
    }

    //#region Render

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

    renderToolbarSelected(): SlottedTemplateResult {
        return guard(
            [this.selectedMap.size],
            () =>
                html` <button
                    ?disabled=${!this.selectedMap.size}
                    type="button"
                    class="pf-c-button pf-m-danger"
                    @click=${() => {
                        const api = new CoreApi(DEFAULT_CONFIG);

                        return renderDeleteBulkFormModal<Application>({
                            ".objectLabel": msg("Application(s)"),
                            ".objects": this.selectedElements,
                            ".usedBy": (item) =>
                                api.coreApplicationsUsedByList({
                                    slug: item.slug,
                                }),
                            ".delete": (item: Application) =>
                                api.coreApplicationsDestroy({
                                    slug: item.slug,
                                }),
                        });
                    }}
                >
                    ${msg("Delete")}
                </button>`,
        );
    }

    row(item: Application): SlottedTemplateResult[] {
        return [
            html`<ak-app-icon
                aria-label=${msg(str`Application icon for "${item.name}"`)}
                name=${item.name}
                icon=${ifPresent(item.metaIconUrl)}
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
                <button
                    type="button"
                    class="pf-c-button pf-m-plain"
                    value=${item.pk}
                    @click=${renderEditApplicationForm.bind(null, item.slug)}
                    aria-label=${msg(str`Edit "${item.name}"`)}
                >
                    <pf-tooltip position="top" content=${msg("Edit")} trigger="mouseenter">
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
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

    renderObjectCreate() {
        // return html`<ak-application-wizard .open=${getURLParam("createWizard", false)}>
        //         <button
        //             slot="trigger"
        //             class="pf-c-button pf-m-primary"
        //             data-ouia-component-id="start-application-wizard"
        //         >
        //             ${msg("Create with Provider")}
        //         </button>
        //     </ak-application-wizard>
        return html`
            <button @click=${renderCreateApplicationForm} class="pf-c-button pf-m-primary">
                ${msg("Create")}
            </button>
        `;
    }

    renderToolbar(): TemplateResult {
        if (Date.now()) return super.renderToolbar();
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

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-list": ApplicationListPage;
    }
}
