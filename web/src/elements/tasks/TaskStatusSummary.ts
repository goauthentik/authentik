import "#elements/cards/AggregateCard";
import "#elements/Spinner";

import { AKElement } from "#elements/Base";

import { GlobalTaskStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-task-status-summary")
export class TaskStatusSummary extends AKElement {
    static styles: CSSResult[] = [
        PFGrid,
        PFCard,
        css`
            section {
                padding-block-end: var(--pf-global--spacer--lg);
            }
        `,
    ];

    @property({ attribute: false })
    status?: GlobalTaskStatus;

    render() {
        return html`<section>
            <div
                class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
            >
                <ak-aggregate-card
                    role="status"
                    class="pf-l-grid__item"
                    icon="pf-icon pf-icon-in-progress"
                    label=${msg("Running tasks")}
                >
                    ${this.status
                        ? this.status.running + this.status.preprocess + this.status.postprocess
                        : html`<ak-spinner></ak-spinner>`}
                </ak-aggregate-card>
                <ak-aggregate-card
                    role="status"
                    class="pf-l-grid__item"
                    icon="pf-icon pf-icon-pending"
                    label=${msg("Queued tasks")}
                >
                    ${this.status
                        ? this.status.queued + this.status.consumed
                        : html`<ak-spinner></ak-spinner>`}
                </ak-aggregate-card>
                <ak-aggregate-card
                    role="status"
                    class="pf-l-grid__item"
                    icon="fa fa-check-circle"
                    label=${msg("Successful tasks")}
                >
                    ${this.status
                        ? this.status.done + this.status.info + this.status.warning
                        : html`<ak-spinner></ak-spinner>`}
                </ak-aggregate-card>
                <ak-aggregate-card
                    role="status"
                    class="pf-l-grid__item"
                    icon="fa fa-exclamation-triangle"
                    label=${msg("Error tasks")}
                >
                    ${this.status
                        ? this.status.error + this.status.rejected
                        : html`<ak-spinner></ak-spinner>`}
                </ak-aggregate-card>
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-status-summary": TaskStatusSummary;
    }
}
