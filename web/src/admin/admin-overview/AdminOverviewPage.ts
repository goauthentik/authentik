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
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
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
            PFFlex,
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
        const name = this.user?.user.name ?? this.user?.user.username;

        return html`<ak-page-header description=${msg("General system status")} ?hasIcon=${false}>
                <span slot="header"> ${msg(str`Welcome, ${name || ""}.`)} </span>
            </ak-page-header>

            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    ${this.renderCards()}
                    <div class="pf-l-grid__item pf-m-9-col pf-m-3-row">
                        <ak-recent-events pageSize="6"></ak-recent-events>
                    </div>
                    <div class="pf-l-grid__item pf-m-6-col pf-m-3-col-on-md pf-m-3-col-on-xl">
                        <ak-quick-actions-card .actions=${this.quickActions}>
                        </ak-quick-actions-card>
                    </div>

                    <div class="pf-l-grid__item pf-m-6-col pf-m-3-col-on-md pf-m-3-col-on-xl">
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-zone"
                            header=${msg("Outpost status")}
                            headerLink="#/outpost/outposts"
                        >
                            <ak-admin-status-chart-outpost></ak-admin-status-chart-outpost>
                        </ak-aggregate-card>
                    </div>

                    <div class="pf-l-grid__item pf-m-6-col pf-m-3-col-on-md pf-m-3-col-on-xl">
                        <ak-aggregate-card icon="fa fa-sync-alt" header=${msg("Sync status")}>
                            <ak-admin-status-chart-sync></ak-admin-status-chart-sync>
                        </ak-aggregate-card>
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
