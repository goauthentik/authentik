import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-skip-to-content")
export class AKSkipToContent extends AKElement {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };
    static styles = [
        PFBase,
        css`
            [part="show-on-focus"] {
                position: absolute !important;
                z-index: 99999;
                color: var(--ak-dark-foreground, ButtonText);
                background-color: var(--ak-accent, ButtonFace);
                font-family: var(--pf-global--FontFamily--heading--sans-serif, sans-serif);
                padding: var(--pf-global--spacer--md, 2em);
                border-radius: var(--pf-global--BorderRadius--sm, 3px);
                border-style: dotted;
                border-width: 1px;

                &:not(:focus) {
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    overflow: hidden !important;
                    clip: rect(1px, 1px, 1px, 1px) !important;
                    border: 0 !important;
                }
            }
        `,
    ];

    #targetElement: WeakRef<HTMLElement> | null = null;

    @property({ attribute: false })
    public get targetElement(): HTMLElement | null {
        return this.#targetElement?.deref() ?? null;
    }

    public set targetElement(value: HTMLElement | null) {
        this.#targetElement = value ? new WeakRef(value) : null;
    }

    public activate = () => {
        const { targetElement } = this;

        if (!targetElement) {
            console.warn(`Could not find target element for skip to content`);
            return;
        }

        targetElement.scrollIntoView();
        targetElement.focus?.();
    };

    render() {
        return html`
            <button tabindex="0" @click=${this.activate} type="button" part="show-on-focus">
                ${msg("Skip to content")}
            </button>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-skip-to-content": AKSkipToContent;
    }
}
