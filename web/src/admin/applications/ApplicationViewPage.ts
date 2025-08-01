import "#admin/applications/ApplicationAuthorizeChart";
import "#admin/applications/ApplicationCheckAccessForm";
import "#admin/applications/ApplicationForm";
import "#admin/applications/entitlements/ApplicationEntitlementPage";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/ak-page-header";
import "#components/events/ObjectChangelog";
import "#elements/AppIcon";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import {
    Application,
    CoreApi,
    OutpostsApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-application-view")
export class ApplicationViewPage extends AKElement {
    static styles: CSSResult[] = [
        PFBase,
        PFList,
        PFBanner,
        PFPage,
        PFContent,
        PFButton,
        PFDescriptionList,
        PFGrid,
        PFCard,
    ];

    //#region Properties

    @property({ type: String })
    public applicationSlug?: string;
    //#endregion

    //#region State

    @state()
    protected application?: Application;

    @state()
    protected error?: APIError;

    @state()
    protected missingOutpost = false;

    //#endregion

    //#region Lifecycle

    protected fetchIsMissingOutpost(providersByPk: Array<number>) {
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesList({
                providersByPk,
                pageSize: 1,
            })
            .then((outposts) => {
                if (outposts.pagination.count < 1) {
                    this.missingOutpost = true;
                }
            });
    }

    protected fetchApplication(slug: string) {
        new CoreApi(DEFAULT_CONFIG)
            .coreApplicationsRetrieve({ slug })
            .then((app) => {
                this.application = app;
                if (
                    app.providerObj &&
                    [
                        RbacPermissionsAssignedByUsersListModelEnum.AuthentikProvidersProxyProxyprovider.toString(),
                        RbacPermissionsAssignedByUsersListModelEnum.AuthentikProvidersLdapLdapprovider.toString(),
                    ].includes(app.providerObj.metaModelName)
                ) {
                    this.fetchIsMissingOutpost([app.provider || 0]);
                }
            })
            .catch(async (error) => {
                this.error = await parseAPIResponseError(error);
            });
    }

    public override willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("applicationSlug") && this.applicationSlug) {
            this.fetchApplication(this.applicationSlug);
        }
    }

    //#region Render

    render(): TemplateResult {
        return html`<ak-page-header
                header=${this.application?.name || msg("Loading")}
                description=${ifDefined(this.application?.metaPublisher)}
            >
                <ak-app-icon
                    size=${PFSize.Medium}
                    name=${ifDefined(this.application?.name || undefined)}
                    icon=${ifDefined(this.application?.metaIcon || undefined)}
                    slot="icon"
                ></ak-app-icon>
            </ak-page-header>
            ${this.renderApp()}`;
    }

    renderApp(): TemplateResult {
        if (this.error) {
            return html`<ak-empty-state icon="fa-ban"
                ><span>${msg(str`Failed to fetch application "${this.applicationSlug}".`)}</span>
                <div slot="body">${pluckErrorDetail(this.error)}</div>
            </ak-empty-state>`;
        }

        if (!this.application) {
            return html`<ak-empty-state default-label></ak-empty-state>`;
        }

        return html`<ak-tabs>
            ${this.missingOutpost
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Application is not used by any Outpost.")}
                  </div>`
                : html``}
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${msg("Related")}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list">
                                ${this.application.providerObj
                                    ? html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${msg("Provider")}</span
                                              >
                                          </dt>
                                          <dd class="pf-c-description-list__description">
                                              <div class="pf-c-description-list__text">
                                                  <a
                                                      href="#/core/providers/${this.application
                                                          .providerObj?.pk}"
                                                  >
                                                      ${this.application.providerObj?.name}
                                                      (${this.application.providerObj?.verboseName})
                                                  </a>
                                              </div>
                                          </dd>
                                      </div>`
                                    : html``}
                                ${(this.application.backchannelProvidersObj || []).length > 0
                                    ? html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${msg("Backchannel Providers")}</span
                                              >
                                          </dt>
                                          <dd class="pf-c-description-list__description">
                                              <div class="pf-c-description-list__text">
                                                  <ul class="pf-c-list">
                                                      ${this.application.backchannelProvidersObj.map(
                                                          (provider) => {
                                                              return html`
                                                                  <li>
                                                                      <a
                                                                          href="#/core/providers/${provider.pk}"
                                                                      >
                                                                          ${provider.name}
                                                                          (${provider.verboseName})
                                                                      </a>
                                                                  </li>
                                                              `;
                                                          },
                                                      )}
                                                  </ul>
                                              </div>
                                          </dd>
                                      </div>`
                                    : html``}
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Policy engine mode")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text pf-m-monospace">
                                            ${this.application.policyEngineMode?.toUpperCase()}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Edit")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-forms-modal>
                                                <span slot="submit"> ${msg("Update")} </span>
                                                <span slot="header">
                                                    ${msg("Update Application")}
                                                </span>
                                                <ak-application-form
                                                    slot="form"
                                                    .instancePk=${this.application.slug}
                                                >
                                                </ak-application-form>
                                                <button
                                                    slot="trigger"
                                                    class="pf-c-button pf-m-secondary"
                                                >
                                                    ${msg("Edit")}
                                                </button>
                                            </ak-forms-modal>
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Check access")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                                                <span slot="submit"> ${msg("Check")} </span>
                                                <span slot="header">
                                                    ${msg("Check Application access")}
                                                </span>
                                                <ak-application-check-access-form
                                                    slot="form"
                                                    .application=${this.application}
                                                >
                                                </ak-application-check-access-form>
                                                <button
                                                    slot="trigger"
                                                    class="pf-c-button pf-m-secondary"
                                                >
                                                    ${msg("Test")}
                                                </button>
                                            </ak-forms-modal>
                                        </div>
                                    </dd>
                                </div>
                                ${this.application.launchUrl
                                    ? html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${msg("Launch")}</span
                                              >
                                          </dt>
                                          <dd class="pf-c-description-list__description">
                                              <div class="pf-c-description-list__text">
                                                  <a
                                                      target="_blank"
                                                      href=${this.application.launchUrl}
                                                      slot="trigger"
                                                      class="pf-c-button pf-m-secondary"
                                                  >
                                                      ${msg("Launch")}
                                                  </a>
                                              </div>
                                          </dd>
                                      </div>`
                                    : html``}
                            </dl>
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-10-col-on-xl pf-m-10-col-on-2xl"
                    >
                        <div class="pf-c-card__title">
                            ${msg("Logins over the last week (per 8 hours)")}
                        </div>
                        <div class="pf-c-card__body">
                            ${this.application &&
                            html` <ak-charts-application-authorize
                                application-id=${this.application.pk}
                            >
                            </ak-charts-application-authorize>`}
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Changelog")}</div>
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.application.pk || ""}
                                targetModelApp="authentik_core"
                                targetModelName="application"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </section>
            <section
                slot="page-app-entitlements"
                data-tab-title="${msg("Application entitlements")}"
            >
                <div slot="header" class="pf-c-banner pf-m-info">
                    ${msg("Application entitlements are in preview.")}
                    <a href="mailto:hello+feature/app-ent@goauthentik.io"
                        >${msg("Send us feedback!")}</a
                    >
                </div>
                <div class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">
                            ${msg(
                                "These entitlements can be used to configure user access in this application.",
                            )}
                        </div>
                        <ak-application-entitlements-list .app=${this.application.pk}>
                        </ak-application-entitlements-list>
                    </div>
                </div>
            </section>
            <section
                slot="page-policy-bindings"
                data-tab-title="${msg("Policy / Group / User Bindings")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">
                        ${msg("These policies control which users can access this application.")}
                    </div>
                    <ak-bound-policies-list
                        .target=${this.application.pk}
                        .policyEngineMode=${this.application.policyEngineMode}
                    >
                    </ak-bound-policies-list>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikCoreApplication}
                objectPk=${this.application.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-view": ApplicationViewPage;
    }
}
