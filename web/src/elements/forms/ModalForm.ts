import "#elements/LoadingOverlay";
import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";

import { ModalButton } from "#elements/buttons/ModalButton";
import { ModalHideEvent } from "#elements/controllers/ModalOrchestrationController";
import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";
import { findSlottedInstance } from "#elements/utils/slots";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

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

    @property({ type: Boolean, attribute: "keep-open-after-submit" })
    public keepOpenAfterSubmit = false;

    @property({ type: Boolean })
    public showSubmitButton = true;

    @property({ type: Boolean })
    public loading = false;

    @property({ type: String })
    public cancelText = msg("Cancel");

    //#endregion

    // #region Public methods

    public submit = async (event?: Event): Promise<void> => {
        const form = findSlottedInstance(Form, this.formSlot);

        if (!form) {
            throw new Error(msg("No form found"));
        }

        if (!form.reportValidity()) {
            this.loading = false;
            this.locked = false;

            return;
        }

        this.loading = true;
        this.locked = true;

        const submitter =
            event instanceof SubmitEvent
                ? event.submitter
                : ((event?.currentTarget || this) as HTMLElement);

        const formPromise = form.submit(
            new SubmitEvent("submit", {
                submitter,
            }),
        );

        return formPromise
            .then(() => {
                if (!this.keepOpenAfterSubmit) {
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

    public requestClose = (): void => {
        const defaultInvoked = this.dispatchEvent(new ModalHideEvent(this));

        if (defaultInvoked) {
            this.resetForms();
        }
    };

    //#endregion

    //#region Listeners

    protected refreshListener = (e: Event): void => {
        // if the modal should stay open after successful submit, prevent EVENT_REFRESH from bubbling
        // to the parent components (which would cause table refreshes that destroy the modal)
        if (this.keepOpenAfterSubmit) {
            e.stopPropagation();
        }
    };

    protected scrollListener = () => {
        window.dispatchEvent(
            new CustomEvent("scroll", {
                bubbles: true,
            }),
        );
    };

    protected slotChangeListener = () => {
        const slottedForm = findSlottedInstance(Form, this.formSlot);

        if (!slottedForm) {
            return;
        }

        slottedForm.visible = true;

        this.headingContent = slottedForm.headline || null;
        this.submitButtonContent = slottedForm.submitLabel || null;
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

        this.formSlot.addEventListener("slotchange", this.slotChangeListener);

        this.addEventListener(EVENT_REFRESH, this.refreshListener);
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
                @click=${this.submit}
                class="pf-c-button pf-m-primary"
                aria-description=${msg("Submit action")}
            >
                ${this.submitButtonContent || this.submitSlot}
            </button>`;
        });
    }

    protected renderActions(): SlottedTemplateResult {
        return html`<fieldset class="ak-c-fieldset pf-c-modal-box__footer">
            <legend class="sr-only">${msg("Form actions")}</legend>
            <button
                type="button"
                aria-description=${msg("Cancel action")}
                @click=${this.requestClose}
                class="pf-c-button pf-m-plain"
            >
                ${this.cancelText}
            </button>
            ${this.renderSubmitButton()}
        </fieldset>`;
    }

    protected override renderModalInner(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay topmost></ak-loading-overlay>`
                : nothing}
            ${this.renderHeading()}
            <slot name="above-form"></slot>
            <div class="pf-c-modal-box__body" @scroll=${this.scrollListener}>${this.formSlot}</div>
            ${this.renderActions()}`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-modal": ModalForm;
    }
}
