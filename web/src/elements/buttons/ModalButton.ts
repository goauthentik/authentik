import type { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";
import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import {
    ModalHideEvent,
    ModalShowEvent,
} from "@goauthentik/elements/controllers/ModalOrchestrationController.js";

import { msg } from "@lit/localize";
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
export abstract class ModalButton extends AKElement {
    @property()
    public size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    public open = false;

    @property({ type: Boolean })
    public locked = false;

    static styles: CSSResult[] = [
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
            .pf-c-modal-box.pf-m-xl {
                --pf-c-modal-box--Width: calc(1.5 * var(--pf-c-modal-box--m-lg--lg--MaxWidth));
            }
        `,
    ];

    public resetForms(): void {
        this.querySelectorAll<Form>("[slot=form]").forEach((form) => {
            form.resetForm?.();
        });
    }

    /**
     * Close the modal.
     */
    public close = () => {
        this.resetForms();
        this.open = false;
    };

    /**
     * Show the modal.
     */
    public show = (): void => {
        this.open = true;

        this.dispatchEvent(new ModalShowEvent(this));

        this.querySelectorAll<AKElement>("*").forEach((child) => {
            child.requestUpdate?.();
        });
    };

    #closeListener = () => {
        this.dispatchEvent(new ModalHideEvent(this));
    };

    #backdropListener = (event: PointerEvent) => {
        event.stopPropagation();
    };

    /**
     * @abstract
     */
    protected renderModalInner(): SlottedTemplateResult {
        return html`<slot name="modal"></slot>`;
    }

    /**
     * @abstract
     */
    protected renderModal(): SlottedTemplateResult {
        return html`<div class="pf-c-backdrop" @click=${this.#backdropListener}>
            <div class="pf-l-bullseye">
                <div
                    class="pf-c-modal-box ${this.size} ${this.locked ? "locked" : ""}"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="modal-title"
                    aria-describedby="modal-description"
                >
                    <button
                        @click=${this.#closeListener}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label=${msg("Close dialog")}
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                    ${this.renderModalInner()}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html` <slot name="trigger" @click=${this.show}></slot>
            ${this.open ? this.renderModal() : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-modal-button": ModalButton;
    }
}
