import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";

import { spread } from "@open-wc/lit-helpers";

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";

/**
 * @slot description - Description text above the progress bar, on the left
 * @slot status - Human-readable status above the progress bar, on the right
 */
@customElement("ak-progress-bar")
export class ProgressBar extends AKElement {
    static styles = [
        PFProgress,
        css`
            .pf-c-progress {
                overflow: hidden;
            }
            .pf-c-progress.pf-m-indeterminate {
                --pf-c-progress__bar--Height: 2px;
                --pf-c-progress--GridGap: 0;
                margin-bottom: calc(var(--pf-c-progress__bar--Height) * -1);
                z-index: 1;
                position: relative;
            }
            .pf-c-progress.pf-m-indeterminate .pf-c-progress__bar .pf-c-progress__indicator {
                width: 100%;
                height: 100%;
                animation: indeterminateAnimation 1s infinite linear;
                transform-origin: 0% 50%;
            }
            @keyframes indeterminateAnimation {
                0% {
                    transform: translateX(0) scaleX(0);
                }
                40% {
                    transform: translateX(0) scaleX(0.4);
                }
                100% {
                    transform: translateX(100%) scaleX(0.5);
                }
            }
        `,
    ];

    @property({ type: Number })
    min = 0;
    @property({ type: Number })
    max = 100;
    @property({ type: Number })
    value = 0;

    @property({ type: Boolean })
    indeterminate = false;

    @property()
    size: PFSize = PFSize.Medium;

    render() {
        const barAttrs: { [key: string]: unknown } = {};
        const indicatorAttrs: { [key: string]: unknown } = {};
        if (!this.indeterminate) {
            barAttrs["aria-valuemin"] = this.min;
            barAttrs["aria-valuemax"] = this.max;
            barAttrs["aria-valuenow"] = this.value;
            indicatorAttrs.style = `"width:${Math.min(this.value, 100)}%;";`;
        }
        return html`<div
            class="pf-c-progress ${this.classList} ${this.indeterminate
                ? "pf-m-indeterminate"
                : ""} ${this.size.toString()}"
        >
            ${this.hasSlotted("description")
                ? html`
                      <div class="pf-c-progress__description">
                          <slot name="description"></slot>
                      </div>
                  `
                : nothing}
            ${this.hasSlotted("status")
                ? html`
                      <div class="pf-c-progress__status" aria-hidden="true">
                          <span class="pf-c-progress__measure">
                              <slot name="status"></slot>
                          </span>
                      </div>
                  `
                : nothing}
            <div class="pf-c-progress__bar" role="progressbar" ${spread(barAttrs)}>
                <div class="pf-c-progress__indicator" ${spread(indicatorAttrs)}></div>
            </div>
        </div> `;
    }
}
