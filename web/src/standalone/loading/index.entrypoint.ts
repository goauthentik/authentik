import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

@customElement("ak-loading")
export class Loading extends AKElement {
    static styles = [
        PFSpinner,
        css`
            :host {
                position: absolute;
                inset: 0;
                display: flex;
                flex-flow: column;
                place-items: center;
                justify-content: center;
                text-align: center;
                gap: var(--pf-global--spacer--md);
            }

            label {
                font-size: var(--pf-global--FontSize--xl);
                font-weight: var(--pf-global--FontWeight--normal);
                font-family: var(--pf-global--FontFamily--heading--sans-serif);
            }
        `,
    ];

    public connectedCallback(): void {
        super.connectedCallback();
        this.dataset.akInterfaceRoot = this.tagName.toLowerCase();
    }

    render(): TemplateResult {
        return html`<span class="pf-c-spinner pf-m-xl" aria-hidden="true">
                <span class="pf-c-spinner__clipper"></span>
                <span class="pf-c-spinner__lead-ball"></span>
                <span class="pf-c-spinner__tail-ball"></span>
            </span>
            <label for="progress" class="pf-c-title pf-m-lg">${msg("Loading")}</label>
            <progress
                class="sr-only"
                id="progress"
                aria-valuetext=${msg("Please wait while the content is loading")}
            ></progress>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-loading": Loading;
    }
}
