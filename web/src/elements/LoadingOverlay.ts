import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface ILoadingOverlay {
    topMost?: boolean;
}

/**
 * @class LoadingOverlay
 * @element ak-loading-overlay
 *
 * The LoadingOverlay is meant to cover the container element completely, hiding the content behind
 * a dimming filter, while content loads.
 *
 * @slot "body" - [Optional] message content to display while the overlay is visible.
 */
@customElement("ak-loading-overlay")
export class LoadingOverlay extends AKElement implements ILoadingOverlay {
    /**
     * When true, forces the overlay onto the top layer of the display stack.
     *
     * @attr
     */
    @property({ type: Boolean })
    topMost = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            css`
                :host {
                    display: flex;
                    height: 100%;
                    width: 100%;
                    justify-content: center;
                    align-items: center;
                    position: absolute;
                    background-color: var(--pf-global--BackgroundColor--dark-transparent-200);
                    z-index: 1;
                }
                :host([topMost]) {
                    z-index: 999;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<ak-empty-state loading header="">
            <slot name="body" slot="body"></slot>
        </ak-empty-state>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-loading-overlay": LoadingOverlay;
    }
}
