import "#admin/admin-overview/TopApplicationsTable";
import "#admin/admin-overview/cards/AdminStatusCard";
import "#admin/admin-overview/cards/FipsStatusCard";
import "#admin/admin-overview/cards/RecentEventsCard";
import "#admin/admin-overview/cards/SystemStatusCard";
import "#admin/admin-overview/cards/VersionStatusCard";
import "#admin/admin-overview/cards/WorkerStatusCard";
import "#admin/admin-overview/charts/AdminLoginAuthorizeChart";
import "#admin/admin-overview/charts/OutpostStatusChart";
import "#admin/admin-overview/charts/SyncStatusChart";
import { me } from "#common/users";
import "#components/ak-page-header";
import { AKElement } from "#elements/Base";
import "#elements/cards/AggregatePromiseCard";
import type { QuickAction } from "#elements/cards/QuickActionsCard";
import "#elements/cards/QuickActionsCard";
import { WithLicenseSummary } from "#elements/mixins/license";
import { paramURL } from "#elements/router/RouterOutlet";
import { createReleaseNotesURL } from "@goauthentik/core/version";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionUser } from "@goauthentik/api";

const AdminOverviewBase = WithLicenseSummary(AKElement);

@customElement("ak-admin-overview")
export class AdminOverviewPage extends AdminOverviewBase {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFGrid,
            PFPage,
            PFContent,
            PFDivider,
            css`
                .pf-l-grid__item {
                    height: 100%;
                }
                .pf-l-grid__item.big-graph-container {
                    height: 35em;
                }
                .card-container {
                    max-height: 10em;
                }
                .ak-external-link {
                    display: inline-block;
                    margin-left: 0.175rem;
                    vertical-align: super;
                    line-height: normal;
                    font-size: var(--pf-global--icon--FontSize--sm);
                }
            `,
        ];
    }

    quickActions: QuickAction[] = [
        [msg("Create a new application"), paramURL("/core/applications", { createForm: true })],
        [msg("Check the logs"), paramURL("/events/log")],
        [msg("Explore integrations"), "https://goauthentik.io/integrations/", true],
        [msg("Manage users"), paramURL("/identity/users")],
        [
            msg("Check the release notes"),
            createReleaseNotesURL(import.meta.env.AK_VERSION).href,
            true,
        ],
    ];

    @state()
    user?: SessionUser;

    async firstUpdated(): Promise<void> {
        this.user = await me();
    }

    render(): TemplateResult {
        const username = this.user?.user.name || this.user?.user.username;

        return html` <ak-page-header
                header=${msg(str`Welcome, ${username || ""}.`)}
                description=${msg("General system status")}
                ?hasIcon=${false}
            >
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <!-- row 1 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl pf-l-grid pf-m-gutter"
                    >
                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl">
                            <ak-quick-actions-card .actions=${this.quickActions}>
                            </ak-quick-actions-card>
                        </div>
                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl">
                            <ak-aggregate-card
                                icon="pf-icon pf-icon-zone"
                                header=${msg("Outpost status")}
                                headerLink="#/outpost/outposts"
                            >
                                <ak-admin-status-chart-outpost></ak-admin-status-chart-outpost>
                            </ak-aggregate-card>
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-4-col-on-2xl"
                        >
                            <ak-aggregate-card icon="fa fa-sync-alt" header=${msg("Sync status")}>
                                <ak-admin-status-chart-sync></ak-admin-status-chart-sync>
                            </ak-aggregate-card>
                        </div>
                        <div class="pf-l-grid__item pf-m-12-col">
                            <hr class="pf-c-divider" />
                        </div>
                        ${this.renderCards()}
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl">
                        <ak-recent-events pageSize="6"></ak-recent-events>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col">
                        <hr class="pf-c-divider" />
                    </div>
                    <!-- row 3 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-8-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-server"
                            header=${msg(
                                "Logins and authorizations over the last week (per 8 hours)",
                            )}
                        >
                            <ak-charts-admin-login-authorization></ak-charts-admin-login-authorization>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-server"
                            header=${msg("Apps with most usage")}
                        >
                            <ak-top-applications-table></ak-top-applications-table>
                        </ak-aggregate-card>
                    </div>
                </div>
            </section>`;
    }

    renderCards() {
        const isEnterprise = this.hasEnterpriseLicense;
        const classes = {
            "card-container": true,
            "pf-l-grid__item": true,
            "pf-m-6-col": true,
            "pf-m-4-col-on-md": !isEnterprise,
            "pf-m-4-col-on-xl": !isEnterprise,
            "pf-m-3-col-on-md": isEnterprise,
            "pf-m-3-col-on-xl": isEnterprise,
        };

        return html`<div class=${classMap(classes)}>
                <ak-admin-status-system> </ak-admin-status-system>
            </div>
            <div class=${classMap(classes)}>
                <ak-admin-status-version> </ak-admin-status-version>
            </div>
            <div class=${classMap(classes)}>
                <ak-admin-status-card-workers> </ak-admin-status-card-workers>
            </div>
            ${isEnterprise
                ? html` <div class=${classMap(classes)}>
                      <ak-admin-fips-status-system> </ak-admin-fips-status-system>
                  </div>`
                : nothing} `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-overview": AdminOverviewPage;
    }
}
