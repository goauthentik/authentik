import "#elements/LoadingOverlay";
import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";

import { ModalButton } from "#elements/buttons/ModalButton";
import { ModalHideEvent } from "#elements/controllers/ModalOrchestrationController";
import { Form } from "#elements/forms/Form";
import {
    AbstractLitElementConstructor,
    LitElementConstructor,
    SlottedTemplateResult,
} from "#elements/types";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

function findSlottedInstance<T>(
    NodeConstructor: LitElementConstructor<T> | AbstractLitElementConstructor<T>,
    slot: HTMLSlotElement,
): T | null {
    const assignedNodes = slot.assignedNodes({ flatten: true });

    const node = assignedNodes.find((node) => node instanceof NodeConstructor);

    return node ? (node as T) : null;
}

@customElement("ak-forms-modal")
export class ModalForm extends ModalButton {
    /**
     * A required slot containing the form to be displayed in the modal.
     */
    protected readonly formSlot: HTMLSlotElement;
    /**
     * An optional slot containing the heading of the modal.
     *
     * @see {@link renderHeading}
     */
    protected readonly headingSlot: HTMLSlotElement;

    /**
     * An optional slot containing the submit button content.
     *
     * @see {@link renderSubmitButton}
     */
    protected readonly submitSlot: HTMLSlotElement;

    /**
     * The heading of the modal.
     *
     * This is either provided via the "header" slot or inferred from the slotted form's headline.
     */
    @state()
    protected headingContent: SlottedTemplateResult = null;

    /**
     * The heading of the modal.
     *
     * This is either provided via the "header" slot or inferred from the slotted form's headline.
     */
    @state()
    protected submitButtonContent: SlottedTemplateResult = null;

    //#region Properties

    @property({ type: Boolean })
    public closeAfterSuccessfulSubmit = true;

    @property({ type: Boolean })
    public showSubmitButton = true;

    @property({ type: Boolean })
    public loading = false;

    @property({ type: String })
    public cancelText = msg("Cancel");

    //#endregion

    // #region Private methods

    #confirm = async (): Promise<void> => {
        const form = this.querySelector<Form>("[slot=form]");

        if (!form) {
            throw new Error(msg("No form found"));
        }

        if (!(form instanceof Form)) {
            console.warn("authentik/forms: form inside the form slot is not a Form", form);
            throw new Error(msg("Element inside the form slot is not a Form"));
        }

        if (!form.reportValidity()) {
            this.loading = false;
            this.locked = false;

            return;
        }

        this.loading = true;
        this.locked = true;

        const formPromise = form.submit(
            new SubmitEvent("submit", {
                submitter: this,
            }),
        );

        return formPromise
            .then(() => {
                if (this.closeAfterSuccessfulSubmit) {
                    this.open = false;
                    form?.reset();

                    // TODO: We may be fetching too frequently.
                    // Repeat dispatching will prematurely abort refresh listeners and cause several fetches and re-renders.
                    this.dispatchEvent(
                        new CustomEvent(EVENT_REFRESH, {
                            bubbles: true,
                            composed: true,
                        }),
                    );
                }

                this.loading = false;
                this.locked = false;
            })
            .catch((error: unknown) => {
                this.loading = false;
                this.locked = false;

                throw error;
            });
    };

    #cancel = (): void => {
        const defaultInvoked = this.dispatchEvent(new ModalHideEvent(this));

        if (defaultInvoked) {
            this.resetForms();
        }
    };

    //#endregion

    //#region Listeners

    #refreshListener = (e: Event): void => {
        // if the modal should stay open after successful submit, prevent EVENT_REFRESH from bubbling
        // to the parent components (which would cause table refreshes that destroy the modal)
        if (!this.closeAfterSuccessfulSubmit) {
            e.stopPropagation();
        }
    };

    #scrollListener = () => {
        window.dispatchEvent(
            new CustomEvent("scroll", {
                bubbles: true,
            }),
        );
    };

    //#endregion

    //#region Lifecycle

    constructor() {
        super();

        this.formSlot = this.ownerDocument.createElement("slot");
        this.formSlot.name = "form";

        this.headingSlot = this.ownerDocument.createElement("slot");
        // TODO: change to heading to match PF5 convention.
        this.headingSlot.name = "header";

        this.submitSlot = this.ownerDocument.createElement("slot");
        this.submitSlot.name = "submit";

        this.formSlot.addEventListener("slotchange", () => {
            const slottedForm = this.hasSlotted("header")
                ? null
                : findSlottedInstance(Form, this.formSlot);

            this.headingContent = slottedForm?.headline || null;
            this.submitButtonContent = slottedForm?.actionLabel || null;
        });

        this.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    //#endregion

    //#region Rendering

    protected renderHeading(): SlottedTemplateResult {
        return guard([this.headingContent], () => {
            return html`<header class="pf-c-modal-box__header">
                <h1 id="modal-title" class="pf-c-modal-box__title">
                ${this.headingContent || this.headingSlot}</h1>
            </div>
        </header>`;
        });
    }

    protected renderSubmitButton(): SlottedTemplateResult {
        return guard([this.showSubmitButton, this.submitButtonContent], () => {
            if (!this.showSubmitButton) {
                return nothing;
            }

            return html`<button
                type="button"
                @click=${this.#confirm}
                class="pf-c-button pf-m-primary"
                aria-description=${msg("Submit action")}
            >
                ${this.submitButtonContent || this.submitSlot}
            </button>`;
        });
    }

    protected override renderModalInner(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay topmost></ak-loading-overlay>`
                : nothing}
            ${this.renderHeading()}
            <slot name="above-form"></slot>
            <div class="pf-c-modal-box__body" @scroll=${this.#scrollListener}>${this.formSlot}</div>
            <fieldset class="pf-c-modal-box__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                ${this.renderSubmitButton()}
                <button
                    type="button"
                    aria-description=${msg("Cancel action")}
                    @click=${this.#cancel}
                    class="pf-c-button pf-m-secondary"
                >
                    ${this.cancelText}
                </button>
            </fieldset>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-modal": ModalForm;
    }
}
