import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import {
    ModalHideEvent,
    ModalShowEvent,
} from "@goauthentik/elements/controllers/ModalOrchestrationController.js";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

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

export const MODAL_BUTTON_STYLES = css`
    :host {
        text-align: left;
        font-size: var(--pf-global--FontSize--md);
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
export class ModalButton extends AKElement {
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
            MODAL_BUTTON_STYLES,
            css`
                .locked {
                    overflow-y: hidden !important;
                }
            `,
        ];
    }

    closeModal() {
        this.resetForms();
        this.open = false;
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
        this.dispatchEvent(new ModalShowEvent(this));
        this.querySelectorAll("*").forEach((child) => {
            if ("requestUpdate" in child) {
                (child as AKElement).requestUpdate();
            }
        });
    }

    renderModalInner(): TemplateResult | typeof nothing {
        return html`<slot name="modal"></slot>`;
    }

    renderModal(): TemplateResult {
        return html`<div
            class="pf-c-backdrop"
            @click=${(e: PointerEvent) => {
                e.stopPropagation();
            }}
        >
            <div class="pf-l-bullseye">
                <div
                    class="pf-c-modal-box ${this.size} ${this.locked ? "locked" : ""}"
                    role="dialog"
                    aria-modal="true"
                >
                    <button
                        @click=${() => {
                            this.dispatchEvent(new ModalHideEvent(this));
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
            ${this.open ? this.renderModal() : nothing}`;
    }
}
