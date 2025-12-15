import "#elements/LoadingOverlay";
import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";

import { ModalButton } from "#elements/buttons/ModalButton";
import { ModalHideEvent } from "#elements/controllers/ModalOrchestrationController";
import { Form } from "#elements/forms/Form";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-forms-modal")
export class ModalForm extends ModalButton {
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
                    form.reset();

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
            .catch(() => {
                this.loading = false;
                this.locked = false;
            });
    };

    #cancel = (): void => {
        const defaultInvoked = this.dispatchEvent(new ModalHideEvent(this));

        if (defaultInvoked) {
            this.resetForms();
        }
    };

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

    override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    protected renderModalInner(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay topmost></ak-loading-overlay>`
                : nothing}
            <section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 id="modal-title" class="pf-c-title pf-m-2xl">
                        <slot name="header"></slot>
                    </h1>
                </div>
            </section>
            <slot name="above-form"></slot>
            <section class="pf-c-modal-box__body" @scroll=${this.#scrollListener}>
                <slot name="form"></slot>
            </section>
            <fieldset class="pf-c-modal-box__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                ${this.showSubmitButton
                    ? html`<button
                          type="button"
                          @click=${this.#confirm}
                          class="pf-c-button pf-m-primary"
                          aria-description=${msg("Submit action")}
                      >
                          <slot name="submit"></slot>
                      </button>`
                    : nothing}
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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-modal": ModalForm;
    }
}
