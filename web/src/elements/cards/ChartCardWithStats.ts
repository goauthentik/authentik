import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import { EventChart } from "#elements/charts/EventChart";
import CardStyles from "#elements/cards/AggregateCard.css";
import { SlottedTemplateResult } from "#elements/types";

import { EventVolume } from "@goauthentik/api";

import { ChartData } from "chart.js";

import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

export interface ChartCardStat {
    label: string;
    value: string;
    delta?: string;
    tone?: "success" | "danger" | "warning";
}

/**
 * Abstract base class for an event-volume chart with a row of big-number
 * stats above it, rendered in an `ak-aggregate-card`-styled shell.
 *
 * Subclasses implement `apiRequest`/`getStats`/`getChartDatasets` the same
 * way an `EventChart` subclass implements `apiRequest`/`getChartData`.
 */
export abstract class ChartCardWithStats extends EventChart {
    @property({ type: String })
    public icon: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    @property({ type: String })
    public headerLink: string | null = null;

    @state()
    protected stats: ChartCardStat[] = [];

    abstract getStats(data: EventVolume[]): ChartCardStat[];
    abstract getChartDatasets(data: EventVolume[]): ChartData;

    getChartData(data: EventVolume[]): ChartData {
        this.stats = this.getStats(data);

        return this.getChartDatasets(data);
    }

    public static styles: CSSResult[] = [
        ...super.styles,
        PFCard,
        PFFlex,
        CardStyles,
        css`
            .chart-card-body {
                display: flex;
                flex-direction: column;
            }
            .chart-slot {
                display: flex;
                flex: 1;
                flex-direction: column;
                min-height: 0;
            }
            .stats-row {
                display: grid;
                grid-auto-flow: column;
                gap: var(--pf-global--spacer--2xl);
                padding-left: var(--pf-global--spacer--xs);
                padding-bottom: var(--pf-global--spacer--md);
                margin-bottom: var(--pf-global--spacer--md);
                border-bottom: 1px solid var(--pf-global--BorderColor--100);
            }
            .stat {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--xs);
            }
            .stat-label {
                font-size: var(--pf-global--FontSize--sm);
                color: var(--pf-global--Color--200);
            }
            .stat-value {
                font-size: var(--pf-global--FontSize--2xl);
            }
            .stat-delta {
                font-size: var(--pf-global--FontSize--xs);
            }
            .stat-delta.pf-m-success {
                color: var(--pf-global--success-color--100);
            }
            .stat-delta.pf-m-danger {
                color: var(--pf-global--danger-color--100);
            }
            .stat-delta.pf-m-warning {
                color: var(--pf-global--warning-color--100);
            }
        `,
    ];

    renderStats(): SlottedTemplateResult {
        if (!this.stats.length) {
            return nothing;
        }

        return html`<div class="stats-row">
            ${this.stats.map(
                (stat) => html`<div class="stat">
                    <span class="stat-label">${stat.label}</span>
                    <span class="stat-value">${stat.value}</span>
                    ${
                        stat.delta
                            ? html`<span class="stat-delta ${stat.tone ? `pf-m-${stat.tone}` : ""}"
                                  >${stat.delta}</span
                              >`
                            : nothing
                    }
                </div>`,
            )}
        </div>`;
    }

    render(): TemplateResult {
        return html`<section class="pf-c-card pf-c-card-aggregate">
            <header class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between">
                <h1 class="pf-c-card__title">
                    ${this.icon ? html`<i aria-hidden="true" class="${this.icon}"></i>` : nothing}
                    <span>${this.label || nothing}</span>
                    ${
                        this.headerLink
                            ? html`<a href="${this.headerLink}"
                                  ><i aria-hidden="true" class="fa fa-link"></i
                              ></a>`
                            : nothing
                    }
                </h1>
            </header>
            <div class="pf-c-card__body chart-card-body">
                ${this.renderStats()}
                <div class="chart-slot">${super.render()}</div>
            </div>
        </section>`;
    }
}
