import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import AKGlobal from "../../authentik.css";
import { SpinnerSize } from "../Spinner";
import { PRIMARY_CLASS, PROGRESS_CLASS } from "../../constants";

@customElement("ak-spinner-button")
export class SpinnerButton extends LitElement {
    @property({type: Boolean})
    isRunning = false;

    @property()
    form?: string;

    @property()
    callAction: () => void = this.defaultCallAction;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFSpinner,
            AKGlobal,
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
        this.classList.add(PRIMARY_CLASS);
    }

    setLoading(): void {
        this.isRunning = true;
        this.classList.add(PROGRESS_CLASS);
        this.requestUpdate();
    }

    setDone(statusClass: string): void {
        this.isRunning = false;
        this.classList.remove(PROGRESS_CLASS);
        this.classList.replace(PRIMARY_CLASS, statusClass);
        this.requestUpdate();
        setTimeout(() => {
            this.classList.replace(statusClass, PRIMARY_CLASS);
            this.requestUpdate();
        }, 1000);
    }

    defaultCallAction(): void {
        if (this.isRunning === true) {
            return;
        }
        if (this.form) {
            // Since the form= attribute is only used within a modal button,
            // we can assume the form is always two levels up
            this.parentElement?.parentElement?.querySelector<HTMLFormElement>(`#${this.form}`)?.dispatchEvent(new Event("submit", {
                bubbles: true,
                cancelable: true,
            }));
        }
        this.setLoading();
    }

    render(): TemplateResult {
        return html`<button
            class="pf-c-button pf-m-progress ${this.classList.toString()}"
            @click=${() => this.callAction()}
        >
            ${this.isRunning
                ? html` <span class="pf-c-button__progress">
                            <ak-spinner size=${SpinnerSize.Medium}></ak-spinner>
                        </span>`
                : ""}
            <slot></slot>
        </button>`;
    }
}
