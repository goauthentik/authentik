import "#admin/admin-overview/cards/TopApplicationsTable";
import "#admin/admin-overview/cards/AdminStatusCard";
import "#admin/admin-overview/cards/FipsStatusCard";
import "#admin/admin-overview/cards/RecentEventsCard";
import "#admin/admin-overview/cards/SystemStatusCard";
import "#admin/admin-overview/cards/VersionStatusCard";
import "#admin/admin-overview/cards/WorkerStatusCard";
import "#admin/admin-overview/charts/AdminLoginAuthorizeChart";
import "#admin/admin-overview/cards/OutpostStatusCard";
import "#admin/admin-overview/cards/SyncStatusCard";
import "#elements/cards/AggregateCard";
import "#elements/cards/QuickActionsCard";
import "#elements/Divider";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import type { QuickAction } from "#elements/cards/QuickActionsCard";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import { toAdminInterface } from "#elements/router/core/interfaces";

import { setPageDetails } from "#components/ak-page-navbar";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

const AdminOverviewBase = WithLicenseSummary(WithSession(AKElement));

@customElement("ak-admin-overview")
export class AdminOverviewPage extends AdminOverviewBase {
    static styles: CSSResult[] = [
        PFGrid,
        PFPage,
        PFContent,
        css`
            .page-rows {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--gutter);
                /* ak-page-navbar's height isn't inheritable here (it's a sibling of
                   .pf-c-page__main, not an ancestor), so it's hardcoded to match
                   its --ak-c-page-navbar--Height default. Falls short only below
                   the ~768px breakpoint, where the navbar grows to fit wrapped
                   content; the bottom-row min-height floor keeps it from breaking. */
                min-height: calc(
                    100dvh - 7.5rem - var(--pf-c-page__main-section--PaddingTop) -
                        var(--pf-c-page__main-section--PaddingBottom)
                );
            }
            .pf-l-grid__item {
                height: 100%;
            }
            .login-chart-row {
                min-height: 30em;
            }
            .bottom-row {
                flex: 1;
                min-height: 25em;
                align-content: stretch;
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
        [
            msg("Create a new application"),
            toAdminInterface("core/applications", { "create-wizard": "application" }),
        ],
        [msg("Check the logs"), toAdminInterface("events/log")],
        [msg("Explore integrations"), "https://integrations.goauthentik.io/", true],
        [msg("Manage users"), toAdminInterface("identity/users")],
        [msg("Check the release notes"), import.meta.env.AK_DOCS_RELEASE_NOTES_URL, true],
    ];

    render(): TemplateResult {
        return html` <main class="pf-c-page__main-section" aria-label=${msg("Overview")}>
            <div class="page-rows">
                <!-- row 1: status cards -->
                <div class="pf-l-grid pf-m-gutter">${this.renderCards()}</div>
                <ak-divider></ak-divider>
                <!-- row 2: login chart, full width -->
                <div class="pf-l-grid pf-m-gutter login-chart-row">
                    <div class="pf-l-grid__item pf-m-12-col">
                        <ak-charts-admin-login-authorization></ak-charts-admin-login-authorization>
                    </div>
                </div>
                <ak-divider></ak-divider>
                <!-- row 3: recent events (50%) / apps with most usage (33%) / quick actions (17%) -->
                <div class="pf-l-grid pf-m-gutter bottom-row">
                    <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl">
                        <ak-recent-events></ak-recent-events>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col pf-m-4-col-on-xl">
                        <ak-top-applications-table></ak-top-applications-table>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl">
                        <ak-quick-actions-card .actions=${this.quickActions}>
                        </ak-quick-actions-card>
                    </div>
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
            "pf-m-4-col-on-md": true,
            "pf-m-2-col-on-xl": true,
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
            ${
                isEnterprise
                    ? html` <div class=${classMap(classes)}>
                          <ak-admin-fips-status-system> </ak-admin-fips-status-system>
                      </div>`
                    : nothing
            }
            <div class=${classMap(classes)}>
                <ak-admin-status-card-outpost></ak-admin-status-card-outpost>
            </div>
            <div class=${classMap(classes)}>
                <ak-admin-status-card-sync></ak-admin-status-card-sync>
            </div>`;
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
