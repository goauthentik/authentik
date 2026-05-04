import "#admin/applications/ApplicationAuthorizeChart";
import "#admin/applications/ApplicationCheckAccessForm";
import "#admin/applications/ApplicationForm";
import "#admin/applications/entitlements/ApplicationEntitlementPage";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/lifecycle/ObjectLifecyclePage";
import "#admin/events/ObjectChangelog";
import "#elements/AppIcon";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#admin/applications/ApplicationEvents";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { WithLicenseSummary } from "#elements/mixins/license";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { ApplicationCheckAccessForm } from "#admin/applications/ApplicationCheckAccessForm";
import { ApplicationForm } from "#admin/applications/ApplicationForm";

import {
    Application,
    ContentTypeEnum,
    CoreApi,
    EventActions,
    EventsApi,
    EventStats,
    ModelEnum,
    OutpostsApi,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-application-view")
export class ApplicationViewPage extends WithLicenseSummary(AKElement) {
    static styles: CSSResult[] = [
        PFList,
        PFBanner,
        PFPage,
        PFContent,
        PFButton,
        PFDescriptionList,
        PFGrid,
        PFFlex,
        PFCard,
        css`
            .big-number {
                font-size: 250%;
            }
        `,
    ];

    //#region Properties

    @property({ type: String })
    public applicationSlug?: string;
    //#endregion

    //#region State

    @state()
    protected application?: Application;

    @state()
    protected stats?: EventStats;

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
                        ModelEnum.AuthentikProvidersProxyProxyprovider.toString(),
                        ModelEnum.AuthentikProvidersLdapLdapprovider.toString(),
                    ].includes(app.providerObj.metaModelName)
                ) {
                    this.fetchIsMissingOutpost([app.provider || 0]);
                }
                return new EventsApi(DEFAULT_CONFIG)
                    .eventsEventsStatsRetrieve({
                        action: EventActions.AuthorizeApplication,
                        contextAuthorizedApp: app.pk.replaceAll("-", ""),
                        countSteps: ["hours=24", "days=7", "days=30"],
                    })
                    .then((stats) => {
                        this.stats = stats;
                    });
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

    renderTabOverview() {
        if (!this.application) {
            return nothing;
        }
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl">
                <div class="pf-c-card__title">${msg("Related")}</div>
                <div class="pf-c-card__body">
                    ${renderDescriptionList([
                        [
                            msg("Provider"),
                            this.application.providerObj
                                ? html` <a
                                      href="#/core/providers/${this.application.providerObj?.pk}"
                                  >
                                      ${this.application.providerObj?.name}
                                      (${this.application.providerObj?.verboseName})
                                  </a>`
                                : html`-`,
                        ],
                        [
                            msg("Backchannel Providers"),
                            (this.application.backchannelProvidersObj || []).length > 0
                                ? html`<ul class="pf-c-list">
                                      ${this.application.backchannelProvidersObj.map((provider) => {
                                          return html`
                                              <li>
                                                  <a href="#/core/providers/${provider.pk}">
                                                      ${provider.name} (${provider.verboseName})
                                                  </a>
                                              </li>
                                          `;
                                      })}
                                  </ul>`
                                : html`-`,
                        ],
                        [
                            msg("Policy engine mode"),
                            html`${this.application.policyEngineMode?.toUpperCase()}`,
                        ],
                        [
                            msg("Related actions"),
                            html`<button
                                    class="pf-c-button pf-m-secondary pf-m-block"
                                    ${modalInvoker(ApplicationForm, {
                                        instancePk: this.application.slug,
                                    })}
                                >
                                    ${msg("Edit")}
                                </button>
                                <button
                                    class="pf-c-button pf-m-secondary pf-m-block"
                                    ${modalInvoker(
                                        ApplicationCheckAccessForm,
                                        {
                                            application: this.application,
                                        },
                                        {
                                            closedBy: "closerequest",
                                        },
                                    )}
                                >
                                    ${msg("Check access")}
                                </button>
                                ${this.application.launchUrl
                                    ? html`<a
                                          target="_blank"
                                          href=${this.application.launchUrl}
                                          slot="trigger"
                                          class="pf-c-button pf-m-secondary pf-m-block"
                                      >
                                          ${msg("Launch")}
                                      </a>`
                                    : null}`,
                        ],
                    ])}
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl">
                <div class="pf-c-card__title">${msg("Statistics")}</div>
                <div class="pf-c-card__body">
                    ${renderDescriptionList([
                        [
                            msg("Users"),
                            html`<p class="big-number">
                                ${this.stats ? this.stats?.uniqueUsers : "-"}
                            </p>`,
                        ],
                        [
                            msg("Authorizations (24 hours)"),
                            html`<p class="big-number">
                                ${this.stats ? this.stats?.countStep.hours24 : "-"}
                            </p>`,
                        ],
                        [
                            msg("Authorizations (7 days)"),
                            html`<p class="big-number">
                                ${this.stats ? this.stats?.countStep.days7 : "-"}
                            </p>`,
                        ],
                        [
                            msg("Authorizations (1 month)"),
                            html`<p class="big-number">
                                ${this.stats ? this.stats?.countStep.days30 : "-"}
                            </p>`,
                        ],
                    ])}
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl pf-m-8-col-on-2xl">
                <div class="pf-c-card__title">
                    ${msg("Logins over the last week (per 8 hours)")}
                </div>
                <div class="pf-c-card__body">
                    ${this.application &&
                    html`<ak-charts-application-authorize application-id=${this.application.pk}>
                    </ak-charts-application-authorize>`}
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__title">${msg("Events")}</div>
                <ak-events-application application-id=${this.application.pk || ""}>
                </ak-events-application>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        if (this.error) {
            return html`<ak-empty-state icon="fa-ban"
                ><span>${msg(str`Failed to fetch application "${this.applicationSlug}".`)}</span>
                <div slot="body">${pluckErrorDetail(this.error)}</div>
            </ak-empty-state>`;
        }

        if (!this.application) {
            return html`<ak-empty-state default-label></ak-empty-state>`;
        }

        return html`<main>
            <ak-tabs>
                ${this.missingOutpost
                    ? html`
                          <div
                              slot="header"
                              class="pf-c-banner pf-m-warning"
                              role="status"
                              aria-live="polite"
                          >
                              <div class="pf-l-flex pf-m-space-items-sm">
                                  <div class="pf-l-flex__item">
                                      <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                                  </div>
                                  <div class="pf-l-flex__item">
                                      ${msg("Warning: Application is not used by any Outpost.", {
                                          id: "application.outpost.missing.warning",
                                      })}
                                  </div>
                              </div>
                          </div>
                      `
                    : nothing}
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    ${this.renderTabOverview()}
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-app-entitlements"
                    id="page-app-entitlements"
                    aria-label="${msg("Application entitlements")}"
                >
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
                    role="tabpanel"
                    tabindex="0"
                    slot="page-policy-bindings"
                    id="page-policy-bindings"
                    aria-label="${msg("Policy / Group / User Bindings")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">
                            ${msg(
                                "These policies control which users can access this application.",
                            )}
                        </div>
                        <ak-bound-policies-list
                            .target=${this.application.pk}
                            .policyEngineMode=${this.application.policyEngineMode}
                        >
                        </ak-bound-policies-list>
                    </div>
                </section>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <ak-object-changelog
                            targetModelPk=${this.application.pk || ""}
                            targetModelName=${ModelEnum.AuthentikCoreApplication}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikCoreApplication}
                    objectPk=${this.application.pk}
                ></ak-rbac-object-permission-page>
                ${this.hasEnterpriseLicense
                    ? html`<ak-object-lifecycle-page
                          role="tabpanel"
                          tabindex="0"
                          slot="page-lifecycle"
                          id="page-lifecycle"
                          aria-label=${msg("Lifecycle")}
                          model=${ContentTypeEnum.AuthentikCoreApplication}
                          object-pk=${this.application.pk}
                      ></ak-object-lifecycle-page>`
                    : nothing}
            </ak-tabs>
        </main>`;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            header: this.application?.name ?? msg("Loading application..."),
            description: this.application?.metaPublisher,
            icon: this.application?.metaIconUrl,
            iconImage: true,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-view": ApplicationViewPage;
    }
}
