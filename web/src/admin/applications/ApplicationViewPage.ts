import "@goauthentik/admin/applications/ApplicationAuthorizeChart";
import "@goauthentik/admin/applications/ApplicationCheckAccessForm";
import "@goauthentik/admin/applications/ApplicationForm";
import "@goauthentik/admin/policies/BoundPoliciesList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Application, CoreApi, OutpostsApi } from "@goauthentik/api";

@customElement("ak-application-view")
export class ApplicationViewPage extends AKElement {
    @property()
    set applicationSlug(value: string) {
        new CoreApi(DEFAULT_CONFIG)
            .coreApplicationsRetrieve({
                slug: value,
            })
            .then((app) => {
                this.application = app;
                if (
                    app.providerObj &&
                    [
                        "authentik_providers_proxy.proxyprovider",
                        "authentik_providers_ldap.ldapprovider",
                    ].includes(app.providerObj.metaModelName)
                ) {
                    new OutpostsApi(DEFAULT_CONFIG)
                        .outpostsInstancesList({
                            providersByPk: [app.provider || 0],
                            pageSize: 1,
                        })
                        .then((outposts) => {
                            if (outposts.pagination.count < 1) {
                                this.missingOutpost = true;
                            }
                        });
                }
            });
    }

    @property({ attribute: false })
    application!: Application;

    @state()
    missingOutpost = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFBanner, PFPage, PFContent, PFButton, PFDescriptionList, PFGrid, PFCard];
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon=${this.application?.metaIcon || ""}
                header=${this.application?.name || t`Loading`}
                description=${ifDefined(this.application?.metaPublisher)}
                .iconImage=${true}
            >
            </ak-page-header>
            ${this.renderApp()}`;
    }

    renderApp(): TemplateResult {
        if (!this.application) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<ak-tabs>
            ${this.missingOutpost
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Application is not used by any Outpost.`}
                  </div>`
                : html``}
            <section
                slot="page-overview"
                data-tab-title="${t`Overview`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${t`Related`}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list">
                                ${this.application.providerObj
                                    ? html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${t`Provider`}</span
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
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Policy engine mode`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.application.policyEngineMode?.toUpperCase()}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text">${t`Edit`}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-forms-modal>
                                                <span slot="submit"> ${t`Update`} </span>
                                                <span slot="header">
                                                    ${t`Update Application`}
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
                                                    ${t`Edit`}
                                                </button>
                                            </ak-forms-modal>
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Check access`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                                                <span slot="submit"> ${t`Check`} </span>
                                                <span slot="header">
                                                    ${t`Check Application access`}
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
                                                    ${t`Test`}
                                                </button>
                                            </ak-forms-modal>
                                        </div>
                                    </dd>
                                </div>
                                ${this.application.launchUrl
                                    ? html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${t`Launch`}</span
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
                                                      ${t`Launch`}
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
                            ${t`Logins over the last week (per 8 hours)`}
                        </div>
                        <div class="pf-c-card__body">
                            ${this.application &&
                            html` <ak-charts-application-authorize
                                applicationSlug=${this.application.slug}
                            >
                            </ak-charts-application-authorize>`}
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${t`Changelog`}</div>
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
                slot="page-policy-bindings"
                data-tab-title="${t`Policy / Group / User Bindings`}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">
                        ${t`These policies control which users can access this application.`}
                    </div>
                    <ak-bound-policies-list .target=${this.application.pk}>
                    </ak-bound-policies-list>
                </div>
            </section>
        </ak-tabs>`;
    }
}
