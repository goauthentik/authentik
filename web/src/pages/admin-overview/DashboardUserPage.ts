import "@goauthentik/web/elements/PageHeader";
import "@goauthentik/web/elements/cards/AggregatePromiseCard";
import "@goauthentik/web/elements/charts/AdminModelPerDay";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { EventActions } from "@goauthentik/api";

@customElement("ak-admin-dashboard-users")
export class DashboardUserPage extends LitElement {
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
        return html`<ak-page-header icon="pf-icon pf-icon-user" header=${t`User statistics`}>
            </ak-page-header>
            <section class="pf-c-page__main-section">
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card header=${t`Users created per day in the last month`}>
                            <ak-charts-admin-model-per-day
                                .query=${{
                                    context__model__app: "authentik_core",
                                    context__model__model_name: "user",
                                }}
                            >
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                    <div class="pf-l-grid__item pf-m-12-col row-divider">
                        <hr />
                    </div>
                    <!-- row 2 -->
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card header=${t`Logins per day in the last month`}>
                            <ak-charts-admin-model-per-day action=${EventActions.Login}>
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                    <div
                        class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl big-graph-container"
                    >
                        <ak-aggregate-card header=${t`Failed Logins per day in the last month`}>
                            <ak-charts-admin-model-per-day action=${EventActions.LoginFailed}>
                            </ak-charts-admin-model-per-day>
                        </ak-aggregate-card>
                    </div>
                </div>
            </section> `;
    }
}
