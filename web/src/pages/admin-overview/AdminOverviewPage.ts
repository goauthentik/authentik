import { me } from "@goauthentik/web/api/Users";
import "@goauthentik/web/elements/PageHeader";
import "@goauthentik/web/elements/cards/AggregatePromiseCard";
import "@goauthentik/web/elements/charts/AdminLoginsChart";
import { paramURL } from "@goauthentik/web/elements/router/RouterOutlet";
import "@goauthentik/web/pages/admin-overview/TopApplicationsTable";
import "@goauthentik/web/pages/admin-overview/cards/AdminStatusCard";
import "@goauthentik/web/pages/admin-overview/cards/SystemStatusCard";
import "@goauthentik/web/pages/admin-overview/cards/VersionStatusCard";
import "@goauthentik/web/pages/admin-overview/cards/WorkerStatusCard";
import "@goauthentik/web/pages/admin-overview/charts/FlowStatusChart";
import "@goauthentik/web/pages/admin-overview/charts/GroupCountStatusChart";
import "@goauthentik/web/pages/admin-overview/charts/LDAPSyncStatusChart";
import "@goauthentik/web/pages/admin-overview/charts/OutpostStatusChart";
import "@goauthentik/web/pages/admin-overview/charts/PolicyStatusChart";
import "@goauthentik/web/pages/admin-overview/charts/UserCountStatusChart";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-admin-overview")
export class AdminOverviewPage extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFGrid,
            PFPage,
            PFContent,
            PFList,
            AKGlobal,
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
        return html`<ak-page-header icon="" header="" description=${t`General system status`}>
                <span slot="header">
                    ${until(
                        me().then((user) => {
                            let name = user.user.username;
                            if (user.user.name !== "") {
                                name = user.user.name;
                            }
                            return t`Welcome, ${name}.`;
                        }),
                    )}
                </span>
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <!-- row 1 -->
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
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
                            </ul>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-process-automation"
                            header=${t`Flows`}
                            headerLink="#/flow/flows"
                        >
                            <ak-admin-status-chart-flow></ak-admin-status-chart-flow>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
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
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-user"
                            header=${t`Users`}
                            headerLink="#/identity/users"
                        >
                            <ak-admin-status-chart-user-count></ak-admin-status-chart-user-count>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-users"
                            header=${t`Groups`}
                            headerLink="#/identity/groups"
                        >
                            <ak-admin-status-chart-group-count></ak-admin-status-chart-group-count>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="fa fa-sync-alt"
                            header=${t`LDAP Sync status`}
                            headerLink="#/core/sources"
                        >
                            <ak-admin-status-chart-ldap-sync></ak-admin-status-chart-ldap-sync>
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col row-divider">
                        <hr />
                    </div>
                    <!-- row 2 -->
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                    >
                        <ak-admin-status-system
                            icon="pf-icon pf-icon-server"
                            header=${t`System status`}
                        >
                        </ak-admin-status-system>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                    >
                        <ak-admin-status-version
                            icon="pf-icon pf-icon-bundle"
                            header=${t`Version`}
                            headerLink="https://github.com/goauthentik/authentik/releases"
                        >
                        </ak-admin-status-version>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-4-col-on-xl card-container"
                    >
                        <ak-admin-status-card-workers
                            icon="pf-icon pf-icon-server"
                            header=${t`Workers`}
                        >
                        </ak-admin-status-card-workers>
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
                            header=${t`Logins over the last 24 hours`}
                        >
                            <ak-charts-admin-login></ak-charts-admin-login>
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
