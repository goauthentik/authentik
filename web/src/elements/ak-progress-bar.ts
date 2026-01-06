import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { styleMap } from "lit/directives/style-map.js";

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

            .pf-c-progress.pf-m-indeterminate {
                transition: opacity 0.2s linear;
                transition-delay: 0.2s;

                .pf-c-progress__bar .pf-c-progress__indicator {
                    width: 100%;
                    height: 100%;
                    animation: indeterminateAnimation 1s infinite linear;
                    transform-origin: 0% 50%;
                }
            }

            :host([inert]) .pf-c-progress.pf-m-indeterminate {
                opacity: 0;

                .pf-c-progress__bar .pf-c-progress__indicator {
                    animation-iteration-count: 1;
                }
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

    @property({ type: Number, reflect: true, useDefault: true })
    public min = 0;

    @property({ type: Number, reflect: true, useDefault: true })
    public max = 100;

    @property({ type: Number, reflect: true, useDefault: true })
    public value = 0;

    @property({ type: Boolean, reflect: true, useDefault: true })
    public indeterminate = false;

    @property({ type: String, reflect: true, useDefault: true })
    public size: PFSize = PFSize.Medium;

    @property({ type: String })
    public label = "";

    protected render() {
        return html`<div
            class="pf-c-progress ${this.classList} ${this.indeterminate
                ? "pf-m-indeterminate"
                : ""} ${this.size}"
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
            <div
                class="pf-c-progress__bar ak-fade-in"
                role="progressbar"
                aria-valuemin=${this.min}
                aria-valuemax=${this.max}
                aria-valuenow=${ifPresent(this.indeterminate, this.value)}
                aria-label=${ifPresent(this.label)}
                aria-describedby=${this.hasSlotted("description") ? "description" : nothing}
            >
                <div
                    class="pf-c-progress__indicator"
                    style=${styleMap({
                        width: this.indeterminate ? "100%" : `${Math.min(this.value, 100)}%`,
                    })}
                ></div>
            </div>
        </div> `;
    }
}
