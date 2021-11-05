import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import "../../elements/PageHeader";
import "../../elements/cards/AggregatePromiseCard";
import "../../elements/charts/AdminLoginsChart";
import "./TopApplicationsTable";
import "./cards/AdminStatusCard";
import "./cards/BackupStatusCard";
import "./cards/SystemStatusCard";
import "./cards/VersionStatusCard";
import "./cards/WorkerStatusCard";
import "./charts/FlowStatusChart";
import "./charts/GroupCountStatusChart";
import "./charts/LDAPSyncStatusChart";
import "./charts/OutpostStatusChart";
import "./charts/PolicyStatusChart";
import "./charts/UserCountStatusChart";

@customElement("ak-admin-overview")
export class AdminOverviewPage extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFGrid,
            PFPage,
            PFContent,
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
        return html` <ak-page-header
                icon=""
                header=${t`System Overview`}
                description=${t`General system status`}
            >
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <!-- row 1 -->
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-infrastructure"
                            header=${t`Policies`}
                            headerLink="#/policy/policies"
                        >
                            <ak-admin-status-chart-policy></ak-admin-status-chart-policy>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl pf-m-2-col-on-2xl graph-container"
                    >
                        <ak-aggregate-card
                            icon="pf-icon pf-icon-server"
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
                            icon="fa fa-sync-alt"
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
                            icon="fa fa-sync-alt"
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
                            icon="fa fa-sync-alt"
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
                        class="pf-l-grid__item pf-m-6-col pf-m-3-col-on-md pf-m-3-col-on-xl card-container"
                    >
                        <ak-admin-status-system
                            icon="pf-icon pf-icon-server"
                            header=${t`System status`}
                        >
                        </ak-admin-status-system>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-md pf-m-3-col-on-xl card-container"
                    >
                        <ak-admin-status-version
                            icon="pf-icon pf-icon-bundle"
                            header=${t`Version`}
                            headerLink="https://github.com/goauthentik/authentik/releases"
                        >
                        </ak-admin-status-version>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-2-col-on-md pf-m-3-col-on-xl card-container"
                    >
                        <ak-admin-status-card-backup
                            icon="fa fa-database"
                            header=${t`Backup status`}
                            headerLink="#/administration/system-tasks"
                        >
                        </ak-admin-status-card-backup>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-6-col pf-m-3-col-on-md pf-m-3-col-on-xl card-container"
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
