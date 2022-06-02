import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFBackdrop from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFModalBox from "@patternfly/patternfly/components/ModalBox/modal-box.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PFSize } from "../Spinner";

export const MODAL_BUTTON_STYLES = css`
    :host {
        text-align: left;
        font-size: var(--pf-global--FontSize--md);
    }
    .pf-c-modal-box.pf-m-lg {
        overflow-y: auto;
    }
    .pf-c-modal-box > .pf-c-button + * {
        margin-right: 0;
    }
    /* fix multiple selects height */
    select[multiple] {
        height: 15em;
    }
`;

@customElement("ak-modal-button")
export class ModalButton extends LitElement {
    @property()
    size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    open = false;

    @property({ type: Boolean })
    locked = false;

    handlerBound = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFModalBox,
            PFForm,
            PFTitle,
            PFFormControl,
            PFBullseye,
            PFBackdrop,
            PFPage,
            PFCard,
            PFContent,
            AKGlobal,
            MODAL_BUTTON_STYLES,
            css`
                .locked {
                    overflow-y: hidden !important;
                }
            `,
        ];
    }

    firstUpdated(): void {
        if (this.handlerBound) return;
        window.addEventListener("keyup", this.keyUpHandler);
        this.handlerBound = true;
    }

    keyUpHandler = (e: KeyboardEvent): void => {
        if (e.code === "Escape") {
            this.resetForms();
            this.open = false;
        }
    };

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener("keyup", this.keyUpHandler);
    }

    resetForms(): void {
        this.querySelectorAll<HTMLFormElement>("[slot=form]").forEach((form) => {
            if ("resetForm" in form) {
                form?.resetForm();
            }
        });
    }

    onClick(): void {
        this.open = true;
        this.querySelectorAll("*").forEach((child) => {
            if ("requestUpdate" in child) {
                (child as LitElement).requestUpdate();
            }
        });
    }

    renderModalInner(): TemplateResult {
        return html`<slot name="modal"></slot>`;
    }

    renderModal(): TemplateResult {
        return html`<div class="pf-c-backdrop">
            <div class="pf-l-bullseye">
                <div
                    class="pf-c-modal-box ${this.size} ${this.locked ? "locked" : ""}"
                    role="dialog"
                    aria-modal="true"
                >
                    <button
                        @click=${() => {
                            this.resetForms();
                            this.open = false;
                        }}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label="Close dialog"
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    ${this.renderModalInner()}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${() => this.onClick()}></slot>
            ${this.open ? this.renderModal() : ""}`;
    }
}
