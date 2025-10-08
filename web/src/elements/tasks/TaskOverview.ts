import "#elements/cards/AggregateCard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { GlobalTaskStatus, TasksApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-task-overview")
export class TaskOverview extends AKElement {
    static styles: CSSResult[] = [
        PFBase,
        PFGrid,
        PFCard,
        PFPage,
        css`
            .pf-m-no-padding-bottom {
                padding-bottom: 0;
            }
        `,
    ];

    @state()
    status?: GlobalTaskStatus;

    async firstUpdated() {
        this.status = await new TasksApi(DEFAULT_CONFIG).tasksTasksStatusRetrieve();
    }

    render() {
        if (!this.status) return nothing;
        return html`<section class="pf-c-page__main-section pf-m-no-padding-bottom">
            <div
                class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
            >
                <ak-aggregate-card
                    class="pf-l-grid__item"
                    icon="pf-icon pf-icon-in-progress"
                    label=${msg("Running tasks")}
                >
                    ${this.status.running + this.status.preprocess + this.status.postprocess}
                </ak-aggregate-card>
                <ak-aggregate-card
                    class="pf-l-grid__item"
                    icon="pf-icon pf-icon-pending"
                    label=${msg("Queued tasks")}
                >
                    ${this.status.queued + this.status.consumed}
                </ak-aggregate-card>
                <ak-aggregate-card
                    class="pf-l-grid__item"
                    icon="fa fa-check-circle"
                    label=${msg("Successful tasks")}
                >
                    ${this.status.done + this.status.info + this.status.warning}
                </ak-aggregate-card>
                <ak-aggregate-card
                    class="pf-l-grid__item"
                    icon="fa fa-exclamation-triangle"
                    label=${msg("Error tasks")}
                >
                    ${this.status.error + this.status.rejected}
                </ak-aggregate-card>
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-overview": TaskOverview;
    }
}
