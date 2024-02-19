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
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/cards/AggregatePromiseCard";
import { paramURL } from "@goauthentik/elements/router/RouterOutlet";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SessionUser } from "@goauthentik/api";

export function versionFamily(): string {
    const parts = VERSION.split(".");
    parts.pop();
    return parts.join(".");
}

@customElement("ak-admin-overview")
export class AdminOverviewPage extends AKElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFGrid,
            PFPage,
            PFContent,
            PFList,
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

    @state()
    user?: SessionUser;

    async firstUpdated(): Promise<void> {
        this.user = await me();
    }

    render(): TemplateResult {
        const name = this.user?.user.name ?? this.user?.user.username;
        return html`<ak-page-header icon="" header="" description=${msg("General system status")}>
                <span slot="header"> ${msg(str`Welcome, ${name}.`)} </span>
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <!-- row 1 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl pf-l-grid pf-m-gutter"
                    >
                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-4-col-on-2xl">
                            <ak-aggregate-card
                                icon="fa fa-share"
                                header=${msg("Quick actions")}
                                .isCenter=${false}
                            >
                                <ul class="pf-c-list">
                                    <li>
                                        <a
                                            class="pf-u-mb-xl"
                                            href=${paramURL("/core/applications", {
                                                createForm: true,
                                            })}
                                            >${msg("Create a new application")}</a
                                        >
                                    </li>
                                    <li>
                                        <a class="pf-u-mb-xl" href=${paramURL("/events/log")}
                                            >${msg("Check the logs")}</a
                                        >
                                    </li>
                                    <li>
                                        <a
                                            class="pf-u-mb-xl"
                                            target="_blank"
                                            href="https://goauthentik.io/integrations/"
                                            >${msg("Explore integrations")}<i
                                                class="fas fa-external-link-alt ak-external-link"
                                            ></i
                                        ></a>
                                    </li>
                                    <li>
                                        <a class="pf-u-mb-xl" href=${paramURL("/identity/users")}
                                            >${msg("Manage users")}</a
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
                                            >${msg("Check the release notes")}<i
                                                class="fas fa-external-link-alt ak-external-link"
                                            ></i
                                        ></a>
                                    </li>
                                </ul>
                            </ak-aggregate-card>
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
}
