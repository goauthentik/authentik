import "#elements/cards/AggregateCard";
import "#elements/Spinner";

import { AKElement } from "#elements/Base";

import { GlobalTaskStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

type Status = [string, string, number | null];

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

    get cards(): Status[] {
        return [
            [
                msg("Running tasks"),
                "pf-icon pf-icon-in-progress",
                this.status
                    ? this.status.running + this.status.preprocess + this.status.postprocess
                    : null,
            ],
            [
                msg("Queued tasks"),
                "pf-icon pf-icon-pending",
                this.status ? this.status.queued + this.status.consumed : null,
            ],
            [
                msg("Successful tasks"),
                "fa fa-check-circle",
                this.status ? this.status.done + this.status.info + this.status.warning : null,
            ],
            [
                msg("Error tasks"),
                "fa fa-exclamation-triangle",
                this.status ? this.status.error + this.status.rejected : null,
            ],
        ];
    }

    render() {
        return html`<section>
            <div
                class="pf-l-grid pf-m-gutter pf-m-all-6-col-on-sm pf-m-all-4-col-on-md pf-m-all-3-col-on-lg pf-m-all-3-col-on-xl"
            >
                ${map(
                    this.cards,
                    (c) =>
                        html` <ak-aggregate-card
                            role="status"
                            class="pf-l-grid__item"
                            icon=${c[1]}
                            label=${c[0]}
                            >${c[2] === null ? html`<ak-spinner></ak-spinner>` : c[2]}
                        </ak-aggregate-card>`,
                )}
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-status-summary": TaskStatusSummary;
    }
}
