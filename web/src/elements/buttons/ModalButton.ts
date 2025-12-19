import "#elements/modals/ak-modal";

import { SlottedTemplateResult } from "../types.js";

import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { AKModal } from "#elements/modals/ak-modal";
import { isInteractiveElement } from "#elements/utils/interactivity";
import { isInvokerElement } from "#elements/utils/invokers";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBackdrop from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";

export const MODAL_BUTTON_STYLES = css`
    :host {
        text-align: left;
        font-size: var(--pf-global--FontSize--md);

        /* Fixes issue where browser inherits from modal parent with more restrictive style. */
        cursor: initial;
        user-select: text;
    }
    .ak-modal > .pf-c-button + * {
        margin-right: 0;
    }
    /* fix multiple selects height */
    select[multiple] {
        height: 15em;
    }
`;

@customElement("ak-modal-button")
export abstract class ModalButton extends AKModal {
    static styles: CSSResult[] = [
        PFButton,
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
            .ak-modal.pf-m-xl {
                --ak-modal--Width: calc(1.5 * var(--ak-modal--m-lg--lg--MaxWidth));
            }
        `,
    ];

    //#region Properties

    @property()
    public size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    public locked = false;
    //#endregion

    //#region Public Methods

    public resetForms(): void {
        this.querySelectorAll<Form>("[slot=form]").forEach((form) => {
            form.reset?.();
        });
    }

    /**
     * Close the modal.
     */
    public close = () => {
        this.resetForms();
        this.open = false;
    };

    //#endregion

    // #region Listeners

    #backdropListener = (event: PointerEvent) => {
        event.stopPropagation();
    };

    //#endregion

    //#region Render

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
        return html`<div class="pf-c-backdrop" @click=${this.#backdropListener} role="presentation">
            <div class="pf-l-bullseye" role="presentation">
                <div
                    class="ak-modal ${this.size} ${this.locked ? "locked" : ""}"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="modal-title"
                    aria-describedby="modal-description"
                >
                    <button
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

    public render(): TemplateResult | null {
        return html` ${this.open ? this.renderModal() : nothing} ${this.triggerSlotElement} `;
    }

    protected override shouldRenderModalContent() {
        return true;
    }

    //#endregion

    //#region Lifecycle

    protected triggerSlotElement: HTMLSlotElement;
    protected triggerButtonElement: HTMLElement | null = null;

    protected slotChangeListener = () => {
        if (this.triggerButtonElement) {
            this.triggerButtonElement.removeEventListener("click", this.showListener);
        }

        const assignedElements = this.triggerSlotElement.assignedElements({
            flatten: true,
        });

        const triggerButtonElement = assignedElements.find((element) =>
            isInteractiveElement(element, false),
        );

        if (!triggerButtonElement) {
            return;
        }

        this.triggerButtonElement = triggerButtonElement;

        if (isInvokerElement(this.triggerButtonElement)) {
            this.triggerButtonElement.commandForElement = this.parentElement;
            this.triggerButtonElement.command = "show-modal";
        } else {
            this.triggerButtonElement.addEventListener("click", this.showListener);
        }
    };

    constructor() {
        super();
        this.triggerSlotElement = document.createElement("slot");

        this.triggerSlotElement.name = "trigger";
        this.triggerSlotElement.addEventListener("slotchange", this.slotChangeListener);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-modal-button": ModalButton;
    }
}
