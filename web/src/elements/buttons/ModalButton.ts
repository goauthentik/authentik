import { SlottedTemplateResult } from "../types.js";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";

import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

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

        /* Fixes issue where browser inherits from modal parent with more restrictive style. */
        cursor: initial;
        user-select: text;
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
    //#region Styles

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
            .pf-c-modal-box {
                place-self: center;
                border: none;
                box-shadow: var(--pf-global--BoxShadow--xl);
                width: var(--pf-c-modal-box--m-lg--lg--MaxWidth);

                max-width: var(--pf-c-modal-box--MaxWidth);
                max-height: var(--pf-c-modal-box--MaxHeight);

                &::backdrop {
                    background-color: var(--pf-global--BackgroundColor--dark-transparent-100);
                }
                &:not(:open) {
                    display: none;
                }

                &.pf-m-xl {
                    --pf-c-modal-box--Width: calc(1.5 * var(--pf-c-modal-box--m-lg--lg--MaxWidth));
                }
            }
            .locked {
                overflow-y: hidden !important;
            }
        `,
    ];

    //#endregion

    //#region Properties

    protected closedBy: "any" | "none" | "closerequest" = "any";

    @property()
    public size: PFSize = PFSize.Large;

    @property({ type: Boolean })
    public get open(): boolean {
        return this.#dialogRef.value?.open ?? false;
    }

    public set open(value: boolean) {
        const dialog = this.#dialogRef.value;
        if (!dialog) return;

        if (value) {
            dialog.showModal();
        } else {
            dialog.close();
        }
    }

    @property({ type: Boolean })
    public locked = false;

    // public resetForms(): void {
    //     // this.querySelectorAll<Form>("[slot=form]").forEach((form) => {
    //     //     form.reset?.();
    //     // });
    // }

    //#endregion

    //#region Public methods

    /**
     * Close the modal.
     */
    public close = (returnValue?: string) => {
        this.#dialogRef?.value?.close(returnValue);
    };

    /**
     * Show the modal.
     */
    public show = (): void => {
        this.open = true;

        // this.dispatchEvent(new ModalShowEvent(this));

        // this.querySelectorAll<AKElement>("*").forEach((child) => {
        //     child.requestUpdate?.();
        // });
    };

    //#endregion

    //#region Listeners

    #backdropListener = (event: MouseEvent) => {
        if (!this.open || event.target !== event.currentTarget) return;

        this.open = false;
    };

    //#endregion

    //#region Lifecycle

    #dialogRef = createRef<HTMLDialogElement>();

    //#region Render

    /**
     * @abstract
     */
    protected renderModalInner(): SlottedTemplateResult {
        return html`<slot></slot>`;
    }

    // /**
    //  * @abstract
    //  */
    // protected renderModal(): SlottedTemplateResult {
    // return html`<div class="pf-c-backdrop" @click=${this.#backdropListener} role="presentation">
    //     <div class="pf-l-bullseye" role="presentation">
    //         <div
    //             class="pf-c-modal-box ${this.size} ${this.locked ? "locked" : ""}"
    //             role="dialog"
    //             aria-modal="true"
    //             aria-labelledby="modal-title"
    //             aria-describedby="modal-description"
    //         >
    //             <button
    //                 @click=${this.#closeListener}
    //                 class="pf-c-button pf-m-plain"
    //                 type="button"
    //                 aria-label=${msg("Close dialog")}
    //             >
    //                 <i class="fas fa-times" aria-hidden="true"></i>
    //             </button>
    //             ${this.renderModalInner()}
    //         </div>
    //     </div>
    // </div>`;

    //     return this.();
    // }

    render(): TemplateResult {
        return html`
            <slot name="trigger" @click=${this.show}></slot>
            <dialog
                @mousedown=${this.#backdropListener}
                class="pf-c-modal-box"
                ${ref(this.#dialogRef)}
                aria-labelledby="modal-title"
                aria-describedby="modal-description"
            >
                ${this.open ? this.renderModalInner() : nothing}
            </dialog>
        `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-modal-button": ModalButton;
    }
}
