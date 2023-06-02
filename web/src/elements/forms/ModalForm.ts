import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/elements/LoadingOverlay";
import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { Form } from "@goauthentik/elements/forms/Form";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-forms-modal")
export class ModalForm extends ModalButton {
    @property({ type: Boolean })
    closeAfterSuccessfulSubmit = true;

    @property({ type: Boolean })
    showSubmitButton = true;

    @property({ type: Boolean })
    loading = false;

    @property({ type: String })
    cancelText = msg("Cancel");

    async confirm(): Promise<void> {
        const form = this.querySelector<Form<unknown>>("[slot=form]");
        if (!form) {
            return Promise.reject(msg("No form found"));
        }
        const formPromise = form.submit(new Event("submit"));
        if (!formPromise) {
            return Promise.reject(msg("Form didn't return a promise for submitting"));
        }
        return formPromise
            .then(() => {
                if (this.closeAfterSuccessfulSubmit) {
                    this.open = false;
                    form?.resetForm();
                }
                this.loading = false;
                this.locked = false;
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            })
            .catch((exc) => {
                this.loading = false;
                this.locked = false;
                throw exc;
            });
    }

    renderModalInner(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay ?topMost=${true}></ak-loading-overlay>`
                : html``}
            <section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        <slot name="header"></slot>
                    </h1>
                </div>
            </section>
            <slot name="above-form"></slot>
            <section
                class="pf-c-modal-box__body"
                @scroll=${() => {
                    window.dispatchEvent(
                        new CustomEvent("scroll", {
                            bubbles: true,
                        }),
                    );
                }}
            >
                <slot name="form"></slot>
            </section>
            <footer class="pf-c-modal-box__footer">
                ${this.showSubmitButton
                    ? html`<ak-spinner-button
                              .callAction=${() => {
                                  this.loading = true;
                                  this.locked = true;
                                  return this.confirm();
                              }}
                              class="pf-m-primary"
                          >
                              <slot name="submit"></slot> </ak-spinner-button
                          >&nbsp;`
                    : html``}
                <ak-spinner-button
                    .callAction=${async () => {
                        this.resetForms();
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${this.cancelText}
                </ak-spinner-button>
            </footer>`;
    }
}
