import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import AKGlobal from "../../authentik.css";
import { SpinnerSize } from "../Spinner";
import { ERROR_CLASS, PRIMARY_CLASS, PROGRESS_CLASS, SUCCESS_CLASS } from "../../constants";

@customElement("ak-spinner-button")
export class SpinnerButton extends LitElement {
    @property({type: Boolean})
    isRunning = false;

    @property()
    callAction?: () => Promise<void>;

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

    render(): TemplateResult {
        return html`<button
            class="pf-c-button pf-m-progress ${this.classList.toString()}"
            @click=${() => {
                if (this.isRunning === true) {
                    return;
                }
                this.setLoading();
                if (this.callAction) {
                    this.callAction().then(() => {
                        this.setDone(SUCCESS_CLASS);
                    }).catch(() => {
                        this.setDone(ERROR_CLASS);
                    });
                }
            }}>
            ${this.isRunning
                ? html` <span class="pf-c-button__progress">
                            <ak-spinner size=${SpinnerSize.Medium}></ak-spinner>
                        </span>`
                : ""}
            <slot></slot>
        </button>`;
    }
}
