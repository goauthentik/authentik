import PFLabel from "@patternfly/patternfly/components/Label/label.css";

import { SlottedTemplateResult } from "#elements/types";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";

import { P4Disposition } from "#styles/patternfly/constants";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html } from "lit";

export interface StatusKind {
    label: string;
    color: string;
}

export interface StatusGroup<K extends string> {
    label: string;
    detail: string;
    counts: Partial<Record<K, number>>;
}

const sumCounts = (counts: Partial<Record<string, number>>) =>
    Object.values(counts).reduce<number>((sum, n) => sum + (n ?? 0), 0);

/**
 * Status card showing how many items are OK, a stacked bar of all states, and one row per type.
 */
export abstract class StatusRollupCard<K extends string> extends AdminStatusCard<StatusGroup<K>[]> {
    static styles: CSSResult[] = [
        ...AdminStatusCard.styles,
        PFLabel,
        css`
            .rollup {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
                text-align: start;
                font-size: var(--pf-global--FontSize--sm);
            }
            .summary {
                display: flex;
                align-items: baseline;
                gap: var(--pf-global--spacer--sm);
                color: var(--pf-global--Color--200);
            }
            .summary strong {
                font-family: var(--pf-global--FontFamily--heading--sans-serif);
                font-size: var(--pf-global--FontSize--3xl);
                font-weight: var(--pf-global--FontWeight--normal);
                color: var(--pf-global--Color--100);
            }
            .bar {
                display: flex;
                gap: 2px;
                height: 10px;
            }
            .groups .bar {
                height: 8px;
            }
            .legend {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--md);
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
            }
            .legend li {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--xs);
            }
            .swatch {
                width: 10px;
                height: 10px;
            }
            .groups li {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
                padding-block: var(--pf-global--spacer--sm);
                border-top: var(--pf-global--BorderWidth--sm) solid
                    var(--pf-global--BorderColor--100);
            }
            .group-header {
                display: flex;
                align-items: baseline;
                gap: var(--pf-global--spacer--sm);
            }
            .group-header .detail {
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
            }
        `,
    ];

    /** All states in severity order, mapped to label and color. */
    protected abstract kinds: Record<K, StatusKind>;
    /** States that count as OK in the summary and type badges. */
    protected abstract okKinds: K[];
    protected abstract emptyMessage: string;
    /** Text after the big number, e.g. "of 12 instances healthy". */
    protected abstract summary(total: number): string;

    protected countOk(counts: Partial<Record<K, number>>) {
        return this.okKinds.reduce((sum, k) => sum + (counts[k] ?? 0), 0);
    }

    protected totals(groups: StatusGroup<K>[]) {
        const totals: Partial<Record<K, number>> = {};

        for (const group of groups) {
            for (const k of Object.keys(group.counts) as K[]) {
                totals[k] = (totals[k] ?? 0) + (group.counts[k] ?? 0);
            }
        }

        return totals;
    }

    getStatus(value: StatusGroup<K>[]): Promise<AdminStatus> {
        const totals = this.totals(value);
        const total = sumCounts(totals);
        const bad = total - this.countOk(totals);

        if (total < 1) {
            return Promise.resolve({ icon: "fa fa-info-circle", tone: P4Disposition.Neutral });
        }

        if (bad > 0) {
            return Promise.resolve({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                tone: P4Disposition.Warning,
            });
        }

        return Promise.resolve({
            icon: "fa fa-check-circle pf-m-success",
            tone: P4Disposition.Success,
        });
    }

    protected renderBar(counts: Partial<Record<K, number>>) {
        return html`<div class="bar" aria-hidden="true">
            ${(Object.keys(this.kinds) as K[])
                .filter((k) => counts[k])
                .map(
                    (k) =>
                        html`<div
                            style="flex: ${counts[k]}; background: ${this.kinds[k].color}"
                        ></div>`,
                )}
        </div>`;
    }

    protected renderBadge(counts: Partial<Record<K, number>>) {
        const bad = sumCounts(counts) - this.countOk(counts);

        return bad
            ? html`<span class="pf-c-label pf-m-red pf-m-compact"
                  ><span class="pf-c-label__content"
                      >${msg(str`${bad} need attention`, {
                          id: "admin-overview.status-rollup.badge.attention",
                      })}</span
                  ></span
              >`
            : html`<span class="pf-c-label pf-m-green pf-m-compact"
                  ><span class="pf-c-label__content"
                      >${msg("All OK", { id: "admin-overview.status-rollup.badge.ok" })}</span
                  ></span
              >`;
    }

    renderInner(): SlottedTemplateResult {
        if (!this.status || !this.value) {
            return super.renderInner();
        }

        const totals = this.totals(this.value);
        const total = sumCounts(totals);

        if (total < 1) {
            return html`<p class="subtext">${this.emptyMessage}</p>`;
        }

        return html`<div class="rollup">
            <div class="summary">
                <strong>${this.countOk(totals).toLocaleString()}</strong>
                <span>${this.summary(total)}</span>
            </div>
            ${this.renderBar(totals)}
            <ul class="legend">
                ${(Object.keys(this.kinds) as K[]).map(
                    (k) =>
                        html`<li>
                            <span class="swatch" style="background: ${this.kinds[k].color}"></span>
                            ${this.kinds[k].label} ${(totals[k] ?? 0).toLocaleString()}
                        </li>`,
                )}
            </ul>
            <ul class="groups">
                ${this.value
                    .filter((group) => sumCounts(group.counts) > 0)
                    .map(
                        (group) =>
                            html`<li>
                                <div class="group-header">
                                    <strong>${group.label}</strong>
                                    <span class="detail">${group.detail}</span>
                                    ${this.renderBadge(group.counts)}
                                </div>
                                ${this.renderBar(group.counts)}
                            </li>`,
                    )}
            </ul>
        </div>`;
    }
}
