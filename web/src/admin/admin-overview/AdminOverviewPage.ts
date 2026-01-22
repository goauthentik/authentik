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
import "#elements/cards/AggregatePromiseCard";
import "#elements/cards/QuickActionsCard";

import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import type { QuickAction } from "#elements/cards/QuickActionsCard";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import { paramURL } from "#elements/router/RouterOutlet";

import { setPageDetails } from "#components/ak-page-navbar";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

const AdminOverviewBase = WithLicenseSummary(WithSession(AKElement));

@customElement("ak-admin-overview")
export class AdminOverviewPage extends AdminOverviewBase {
    static styles: CSSResult[] = [
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

    quickActions: QuickAction[] = [
        [msg("Create a new application"), paramURL("/core/applications", { createWizard: true })],
        [msg("Check the logs"), paramURL("/events/log")],
        [msg("Explore integrations"), "https://integrations.goauthentik.io/", true],
        [msg("Manage users"), paramURL("/identity/users")],
        [msg("Check the release notes"), import.meta.env.AK_DOCS_RELEASE_NOTES_URL, true],
    ];

    render(): TemplateResult {
        return html` <main class="pf-c-page__main-section" aria-label=${msg("Overview")}>
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
                            label=${msg("Outpost status")}
                            headerLink="#/outpost/outposts"
                        >
                            <ak-admin-status-chart-outpost></ak-admin-status-chart-outpost>
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-4-col-on-2xl">
                        <ak-aggregate-card
                            icon="fa fa-sync-alt"
                            label=${msg("Sync status")}
                            tooltip=${msg("Integrations synced in the last 12 hours.")}
                        >
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
                        label=${msg("Logins and authorizations over the last week (per 8 hours)")}
                    >
                        <ak-charts-admin-login-authorization></ak-charts-admin-login-authorization>
                    </ak-aggregate-card>
                </div>
                <div
                    class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl big-graph-container"
                >
                    <ak-aggregate-card
                        icon="pf-icon pf-icon-server"
                        label=${msg("Apps with most usage")}
                    >
                        <ak-top-applications-table></ak-top-applications-table>
                    </ak-aggregate-card>
                </div>
            </div>
        </main>`;
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

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        const displayName = formatUserDisplayName(this.currentUser);

        setPageDetails({
            header: displayName ? msg(str`Welcome, ${displayName}`) : msg("Welcome"),
            description: msg("General system status"),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-overview": AdminOverviewPage;
    }
}
