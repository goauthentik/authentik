import "@goauthentik/admin/admin-overview/TopApplicationsTable";
import "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import "@goauthentik/admin/admin-overview/cards/FipsStatusCard";
import "@goauthentik/admin/admin-overview/cards/RecentEventsCard";
import "@goauthentik/admin/admin-overview/cards/SystemStatusCard";
import "@goauthentik/admin/admin-overview/cards/VersionStatusCard";
import "@goauthentik/admin/admin-overview/cards/WorkerStatusCard";
import "@goauthentik/admin/admin-overview/charts/AdminLoginAuthorizeChart";
import "@goauthentik/admin/admin-overview/charts/OutpostStatusChart";
import "@goauthentik/admin/admin-overview/charts/SyncStatusChart";
import { VERSION } from "@goauthentik/common/constants";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider.js";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/cards/AggregatePromiseCard";
import "@goauthentik/elements/cards/QuickActionsCard.js";
import type { QuickAction } from "@goauthentik/elements/cards/QuickActionsCard.js";
import { paramURL } from "@goauthentik/elements/router/RouterOutlet";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";
import { when } from "lit/directives/when.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionUser } from "@goauthentik/api";

export function versionFamily(): string {
    const parts = VERSION.split(".");
    parts.pop();
    return parts.join(".");
}

const RELEASE = `${VERSION.split(".").slice(0, -1).join(".")}#fixed-in-${VERSION.replaceAll(
    ".",
    "",
)}`;

const AdminOverviewBase = WithLicenseSummary(AKElement);

type Renderer = () => TemplateResult | typeof nothing;

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

                .chart-item {
                    aspect-ratio: 2 / 1;
                }
            `,
        ];
    }

    quickActions: QuickAction[] = [
        [msg("Create a new application"), paramURL("/core/applications", { createForm: true })],
        [msg("Check the logs"), paramURL("/events/log")],
        [msg("Explore integrations"), "https://goauthentik.io/integrations/", true],
        [msg("Manage users"), paramURL("/identity/users")],
        [msg("Check the release notes"), `https://goauthentik.io/docs/releases/${RELEASE}`, true],
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
                    <div class="pf-l-grid__item pf-m-12-col pf-m-2-row pf-m-9-col-on-xl">
                        <ak-recent-events pageSize="6"></ak-recent-events>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-xl">
                        <ak-quick-actions-card .actions=${this.quickActions}>
                        </ak-quick-actions-card>
                    </div>

                    <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-sm pf-m-3-col-on-xl">
                        <ak-admin-status-version> </ak-admin-status-version>
                    </div>
                    <div class="pf-l-grid pf-l-grid__item pf-m-12-col pf-m-gutter">
                        ${this.renderSecondaryRow()}

                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-md chart-item">
                            <ak-aggregate-card
                                icon="pf-icon pf-icon-zone"
                                header=${msg("Outpost status")}
                                headerLink="#/outpost/outposts"
                            >
                                <ak-admin-status-chart-outpost></ak-admin-status-chart-outpost>
                            </ak-aggregate-card>
                        </div>
                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-md chart-item">
                            <ak-aggregate-card icon="fa fa-sync-alt" header=${msg("Sync status")}>
                                <ak-admin-status-chart-sync></ak-admin-status-chart-sync>
                            </ak-aggregate-card>
                        </div>
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

    renderSecondaryRow() {
        const isEnterprise = this.hasEnterpriseLicense;
        const colSpan = isEnterprise ? 4 : 6;

        const classes = {
            "card-container": true,
            "pf-l-grid__item": true,
            [`pf-m-12-col`]: true,
            [`pf-m-${colSpan}-col-on-md`]: true,
        };

        return html`
            <div class=${classMap(classes)}>
                <ak-admin-status-system> </ak-admin-status-system>
            </div>

            <div class=${classMap(classes)}>
                <ak-admin-status-card-workers> </ak-admin-status-card-workers>
            </div>

            ${isEnterprise
                ? html`
                      <div class=${classMap(classes)}>
                          <ak-admin-fips-status-system> </ak-admin-fips-status-system>
                      </div>
                  `
                : nothing}
        `;
    }

    renderActions() {
        const release = `${versionFamily()}#fixed-in-${VERSION.replaceAll(".", "")}`;

        const quickActions: [string, string][] = [
            [msg("Create a new application"), paramURL("/core/applications", { createForm: true })],
            [msg("Check the logs"), paramURL("/events/log")],
            [msg("Explore integrations"), "https://goauthentik.io/integrations/"],
            [msg("Manage users"), paramURL("/identity/users")],
            [msg("Check the release notes"), `https://goauthentik.io/docs/releases/${release}`],
        ];

        const action = ([label, url]: [string, string]) => {
            const isExternal = url.startsWith("https://");
            const ex = (truecase: Renderer, falsecase: Renderer) =>
                when(isExternal, truecase, falsecase);

            const content = html`${label}${ex(
                () => html`<i class="fas fa-external-link-alt ak-external-link"></i>`,
                () => nothing,
            )}`;

            return html`<li>
                ${ex(
                    () =>
                        html`<a
                            href="${url}"
                            class="pf-u-mb-xl"
                            rel="noopener noreferrer"
                            target="_blank"
                            >${content}</a
                        >`,
                    () => html`<a href="${url}" class="pf-u-mb-xl" )>${content}</a>`,
                )}
            </li>`;
        };

        return html`${map(quickActions, action)}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-overview": AdminOverviewPage;
    }
}
