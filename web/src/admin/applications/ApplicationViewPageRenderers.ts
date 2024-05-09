import { PFSize } from "@goauthentik/common/enums.js";
import { DescriptionPair, renderDescriptionList } from "@goauthentik/components/DescriptionList.js";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import type { Application, RbacPermissionsAssignedByUsersListModelEnum } from "@goauthentik/api";

export class ApplicationViewPageLoadingRenderer {
    constructor() {}

    render() {
        return html`<ak-page-header header=${msg("Loading")}
            ><ak-empty-state ?loading="${true}" header=${msg("Loading")}> </ak-empty-state
        ></ak-page-header>`;
    }
}

export class ApplicationViewPageRenderer {
    constructor(
        private app: Application,
        private noOutpost: boolean,
        private rbacModel: RbacPermissionsAssignedByUsersListModelEnum,
    ) {}

    missingOutpostMessage() {
        return this.noOutpost
            ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                  ${msg("Warning: Application is not used by any Outpost.")}
              </div>`
            : nothing;
    }

    controlCardContents(app: Application): DescriptionPair[] {
        // prettier-ignore
        const rows: (DescriptionPair | null)[] = [
            app.providerObj
                ? [
                      msg("Provider"),
                      html`
                          <a href="#/core/providers/${app.providerObj?.pk}">
                              ${app.providerObj?.name} (${app.providerObj?.verboseName})
                          </a>
                      `,
                  ]
                : null,

            (app.backchannelProvidersObj || []).length > 0
                ? [
                      msg("Backchannel Providers"),
                      html`
                          <ul class="pf-c-list">
                              ${app.backchannelProvidersObj.map((provider) => {
                                  return html`
                                      <li>
                                          <a href="#/core/providers/${provider.pk}">
                                              ${provider.name} (${provider.verboseName})
                                          </a>
                                      </li>
                                  `;
                              })}
                          </ul>
                      `,
                  ]
                : null,

            [
                msg("Policy engine mode"), 
                app.policyEngineMode?.toUpperCase()
            ],

            [
                msg("Edit"),
                html`
                    <ak-forms-modal>
                        <span slot="submit"> ${msg("Update")} </span>
                        <span slot="header"> ${msg("Update Application")} </span>
                        <ak-application-form slot="form" .instancePk=${app.slug}>
                        </ak-application-form>
                        <button slot="trigger" class="pf-c-button pf-m-secondary">
                            ${msg("Edit")}
                        </button>
                    </ak-forms-modal>
                `,
            ],

            [
                msg("Check access"),
                html`
                    <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                        <span slot="submit"> ${msg("Check")} </span>
                        <span slot="header"> ${msg("Check Application access")} </span>
                        <ak-application-check-access-form slot="form" .application=${app}>
                        </ak-application-check-access-form>
                        <button slot="trigger" class="pf-c-button pf-m-secondary">
                            ${msg("Test")}
                        </button>
                    </ak-forms-modal>
                `,
            ],

            app.launchUrl
                ? [
                      msg("Launch"),
                      html`
                          <a
                              target="_blank"
                              href=${app.launchUrl}
                              slot="trigger"
                              class="pf-c-button pf-m-secondary"
                          >
                              ${msg("Launch")}
                          </a>
                      `,
                  ]
                : null,
        ];

        return rows.filter((row) => row !== null) as DescriptionPair[];
    }

    controlCard(app: Application) {
        return html`
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl">
                <div class="pf-c-card__title">${msg("Related")}</div>
                <div class="pf-c-card__body">
                    ${renderDescriptionList(this.controlCardContents(app))}
                </div>
            </div>
        `;
    }

    loginsChart(app: Application) {
        return html`<div
            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-10-col-on-xl pf-m-10-col-on-2xl"
        >
            <div class="pf-c-card__title">${msg("Logins over the last week (per 8 hours)")}</div>
            <div class="pf-c-card__body">
                ${app &&
                html` <ak-charts-application-authorize applicationSlug=${app.slug}>
                </ak-charts-application-authorize>`}
            </div>
        </div>`;
    }

    changelog(app: Application) {
        return html`
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__title">${msg("Changelog")}</div>
                <div class="pf-c-card__body">
                    <ak-object-changelog
                        targetModelPk=${app.pk || ""}
                        targetModelApp="authentik_core"
                        targetModelName="application"
                    >
                    </ak-object-changelog>
                </div>
            </div>
        `;
    }

    overview(app: Application) {
        return html` 
            <div class="pf-l-grid pf-m-gutter">
                ${this.controlCard(app)} ${this.loginsChart(app)} ${this.changelog(app)}
            </div>
        </section>`;
    }

    policiesList(app: Application) {
        return html`
            <div class="pf-c-card">
                <div class="pf-c-card__title">
                    ${msg("These policies control which users can access this application.")}
                </div>
                <ak-bound-policies-list .target=${app.pk}> </ak-bound-policies-list>
            </div>
        `;
    }

    render() {
        return html` <ak-page-header
                header=${this.app.name}
                description=${ifDefined(this.app.metaPublisher)}
                .iconImage=${true}
            >
                <ak-app-icon size=${PFSize.Medium} slot="icon" .app=${this.app}></ak-app-icon>
            </ak-page-header>
            <ak-tabs>
                ${this.missingOutpostMessage()}
                <section
                    slot="page-overview"
                    data-tab-title="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    ${this.overview(this.app)}
                </section>
                <section
                    slot="page-policy-bindings"
                    data-tab-title="${msg("Policy / Group / User Bindings")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    ${this.policiesList(this.app)}
                </section>
                <ak-rbac-object-permission-page
                    slot="page-permissions"
                    data-tab-title="${msg("Permissions")}"
                    model=${this.rbacModel}
                    objectPk=${this.app.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>`;
    }
}
