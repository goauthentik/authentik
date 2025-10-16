import "#admin/admin-overview/charts/AdminModelPerDay";
import "#elements/cards/AggregatePromiseCard";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { EventActions, EventsEventsVolumeListRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-admin-dashboard-users")
export class DashboardUserPage extends AKElement {
    static styles: CSSResult[] = [
        PFGrid,
        PFPage,
        PFContent,
        PFList,
        PFDivider,
        css`
            .big-graph-container {
                height: 35em;
            }
            .card-container {
                max-height: 10em;
            }
        `,
    ];

    render(): TemplateResult {
        return html`
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card label=${msg("Users created per day in the last month")}>
                            <ak-charts-admin-model-per-day
                                .query=${{
                                    contextModelApp: "authentik_core",
                                    contextModelName: "user",
                                } as EventsEventsVolumeListRequest}
                                label=${msg("Users created")}
                            >
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col">
                        <hr class="pf-c-divider" />
                    </div>
                    <!-- row 2 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card label=${msg("Logins per day in the last month")}>
                            <ak-charts-admin-model-per-day
                                action=${EventActions.Login}
                                label=${msg("Logins")}
                            >
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card label=${msg("Failed Logins per day in the last month")}>
                            <ak-charts-admin-model-per-day
                                action=${EventActions.LoginFailed}
                                label=${msg("Failed logins")}
                            >
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                </div>
            </section>
        `;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-user",
            header: msg("User Statistics"),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-dashboard-users": DashboardUserPage;
    }
}
