import { ERROR_CLASS, PROGRESS_CLASS, SUCCESS_CLASS } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { PFSize } from "@goauthentik/elements/Spinner";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-spinner-button")
export class SpinnerButton extends AKElement {
    @property({ type: Boolean })
    isRunning = false;

    @property()
    callAction?: () => Promise<unknown>;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFSpinner,
            css`
                button {
                    /* Have to use !important here, as buttons with pf-m-progress have transition already */
                    transition: all var(--pf-c-button--m-progress--TransitionDuration) ease 0s !important;
                }
            `,
        ];
    }

    constructor() {
        super();
    }

    setLoading(): void {
        this.isRunning = true;
        this.classList.add(PROGRESS_CLASS);
        this.requestUpdate();
    }

    setDone(statusClass: string): void {
        this.isRunning = false;
        this.classList.remove(PROGRESS_CLASS);
        this.classList.add(statusClass);
        this.requestUpdate();
        setTimeout(() => {
            this.classList.remove(statusClass);
            this.requestUpdate();
        }, 1000);
    }

    render(): TemplateResult {
        return html`<button
            class="pf-c-button pf-m-progress ${this.classList.toString()}"
            @click=${() => {
                if (this.isRunning === true) {
                    return;
                }
                this.setLoading();
                if (this.callAction) {
                    this.callAction()
                        .then(() => {
                            this.setDone(SUCCESS_CLASS);
                        })
                        .catch(() => {
                            this.setDone(ERROR_CLASS);
                        });
                }
            }}
        >
            ${this.isRunning
                ? html`<span class="pf-c-button__progress">
                      <ak-spinner size=${PFSize.Medium}></ak-spinner>
                  </span>`
                : ""}
            <slot></slot>
        </button>`;
    }
}
