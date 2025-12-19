import "#elements/LoadingOverlay";
import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";

import { Form } from "#elements/forms/Form";
import { AKModal } from "#elements/modals/ak-modal";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * Modal specifically designed to host forms.
 */
@customElement("ak-forms-modal")
export class FormsModal extends AKModal {
    //#region Properties

    @property({ type: Boolean, attribute: "close-after-submit", useDefault: true })
    public closeAfterSuccessfulSubmit = true;

    /**
     * @deprecated
     */
    @property({ type: Boolean, attribute: "show-submit", useDefault: true })
    public showSubmitButton = true;

    @property({ type: Boolean, useDefault: true })
    public loading = false;

    public override closeLabel = msg("Cancel");

    //#endregion

    public get form(): Form | null {
        const form = this.#defaultSlot.assignedElements().find((el) => el instanceof Form);

        return form ?? null;
    }

    //#region Private Methods

    #confirm = async (): Promise<void> => {
        const { form } = this;

        if (!form) {
            throw new TypeError(msg("No form found"));
        }

        if (!(form instanceof Form)) {
            console.warn("authentik/forms: form inside the form slot is not a Form", form);
            throw new Error(msg("Element inside the form slot is not a Form"));
        }

        if (!form.reportValidity()) {
            this.loading = false;

            return;
        }

        this.loading = true;

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
            })
            .finally(() => {
                this.loading = false;
            });
    };

    //#endregion

    //#region Lifecycle

    #defaultSlot = this.ownerDocument.createElement("slot");

    public override connectedCallback(): void {
        super.connectedCallback();

        // this.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    //#endregion

    //#region Rendering

    protected renderFormActions(): TemplateResult {
        return html`<fieldset class="ak-modal__footer">
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
                @click=${this.closeListener}
                class="pf-c-button pf-m-secondary"
            >
                ${this.closeLabel}
            </button>
        </fieldset>`;
    }

    protected override render(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay topmost></ak-loading-overlay>`
                : nothing}
            <slot name="above-form"></slot>
            <div class="ak-modal__body">${this.#defaultSlot}</div>
            ${this.renderFormActions()}`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-modal": FormsModal;
    }
}
