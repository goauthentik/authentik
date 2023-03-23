import { AdminInterface } from "@goauthentik/admin/AdminInterface";
import "@goauthentik/admin/admin-overview/TopApplicationsTable";
import "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import "@goauthentik/admin/admin-overview/cards/RecentEventsCard";
import "@goauthentik/admin/admin-overview/cards/SystemStatusCard";
import "@goauthentik/admin/admin-overview/cards/VersionStatusCard";
import "@goauthentik/admin/admin-overview/cards/WorkerStatusCard";
import "@goauthentik/admin/admin-overview/charts/AdminLoginAuthorizeChart";
import "@goauthentik/admin/admin-overview/charts/OutpostStatusChart";
import "@goauthentik/admin/admin-overview/charts/SyncStatusChart";
import { VERSION } from "@goauthentik/common/constants";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/cards/AggregatePromiseCard";
import { paramURL } from "@goauthentik/elements/router/RouterOutlet";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

export function versionFamily(): string {
    const parts = VERSION.split(".");
    parts.pop();
    return parts.join(".");
}

@customElement("ak-admin-overview")
export class AdminOverviewPage extends AKElement {
    static get styles(): CSSResult[] {
        return [
            PFGrid,
            PFPage,
            PFContent,
            PFList,
            css`
                .row-divider {
                    margin-top: -4px;
                    margin-bottom: -4px;
                }
                .graph-container {
                    height: 20em;
                }
                .big-graph-container {
                    height: 35em;
                }
                .card-container {
                    max-height: 10em;
                }
            `,
        ];
    }

    render(): TemplateResult {
        const user = rootInterface<AdminInterface>()?.user;
        let name = user?.user.username;
        if (user?.user.name) {
            name = user.user.name;
        }
        return html`<ak-page-header icon="" header="" description=${t`General system status`}>
                <span slot="header"> ${t`Welcome, ${name}.`} </span>
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <!-- row 1 -->
                    <div class="pf-l-grid__item pf-m-6-col pf-l-grid pf-m-gutter">
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl pf-m-4-col-on-2xl graph-container"
                        >
                            <ak-aggregate-card
                                icon="fa fa-share"
                                header=${t`Quick actions`}
                                .isCenter=${false}
                            >
                                <ul class="pf-c-list">
                                    <li>
                                        <a
                                            class="pf-u-mb-xl"
                                            href=${paramURL("/core/applications", {
                                                createForm: true,
                                            })}
                                            >${t`Create a new application`}</a
                                        >
                                    </li>
                                    <li>
                                        <a class="pf-u-mb-xl" href=${paramURL("/events/log")}
                                            >${t`Check the logs`}</a
                                        >
                                    </li>
                                    <li>
                                        <a
                                            class="pf-u-mb-xl"
                                            target="_blank"
                                            href="https://goauthentik.io/integrations/"
                                            >${t`Explore integrations`}</a
                                        >
                                    </li>
                                    <li>
                                        <a class="pf-u-mb-xl" href=${paramURL("/identity/users")}
                                            >${t`Manage users`}</a
                                        >
                                    </li>
                                    <li>
                                        <a
                                            class="pf-u-mb-xl"
                                            target="_blank"
                                            href="https://goauthentik.io/docs/releases/${versionFamily()}#fixed-in-${VERSION.replaceAll(
                                                ".",
                                                "",
                                            )}"
                                            >${t`Check release notes`}</a
                                        >
                                    </li>
                                </ul>
                            </ak-aggregate-card>
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl pf-m-4-col-on-2xl graph-container"
                        >
                            <ak-aggregate-card
                                icon="pf-icon pf-icon-zone"
                                header=${t`Outpost status`}
                                headerLink="#/outpost/outposts"
                            >
                                <ak-admin-status-chart-outpost></ak-admin-status-chart-outpost>
                            </ak-aggregate-card>
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl pf-m-4-col-on-2xl graph-container"
                        >
                            <ak-aggregate-card icon="fa fa-sync-alt" header=${t`Sync status`}>
                                <ak-admin-status-chart-sync></ak-admin-status-chart-sync>
                            </ak-aggregate-card>
                        </div>
                        <div class="pf-l-grid__item pf-m-12-col row-divider">
                            <hr />
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                        >
                            <ak-admin-status-system> </ak-admin-status-system>
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                        >
                            <ak-admin-status-version> </ak-admin-status-version>
                        </div>
                        <div
                            class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                        >
                            <ak-admin-status-card-workers> </ak-admin-status-card-workers>
                        </div>
                    </div>
                    <div class="pf-l-grid__item pf-m-6-col">
                        <ak-recent-events pageSize="6"></ak-recent-events>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col row-divider">
                        <hr />
                    </div>
                    <!-- row 3 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-8-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-server"
                            header=${t`Logins and authorizations over the last week (per 8 hours)`}
                        >
                            <ak-charts-admin-login-authorization></ak-charts-admin-login-authorization>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-server"
                            header=${t`Apps with most usage`}
                        >
                            <ak-top-applications-table></ak-top-applications-table>
                        </ak-aggregate-card>
                    </div>
                </div>
            </section>`;
    }
}
