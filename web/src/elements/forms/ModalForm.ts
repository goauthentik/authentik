import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/elements/LoadingOverlay";
import { ModalButton } from "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { ModalHideEvent } from "@goauthentik/elements/controllers/ModalOrchestrationController.js";
import { Form } from "@goauthentik/elements/forms/Form";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
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

    #scrollListener = () => {
        window.dispatchEvent(
            new CustomEvent("scroll", {
                bubbles: true,
            }),
        );
    };

    renderModalInner(): TemplateResult {
        return html`${this.loading
                ? html`<ak-loading-overlay topmost></ak-loading-overlay>`
                : nothing}
            <section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        <slot name="header"></slot>
                    </h1>
                </div>
            </section>
            <slot name="above-form"></slot>
            <section class="pf-c-modal-box__body" @scroll=${this.#scrollListener}>
                <slot name="form"></slot>
            </section>
            <footer class="pf-c-modal-box__footer">
                ${this.showSubmitButton
                    ? html`<ak-spinner-button .callAction=${this.#confirm} class="pf-m-primary">
                              <slot name="submit"></slot> </ak-spinner-button
                          >&nbsp;`
                    : nothing}
                <ak-spinner-button .callAction=${this.#cancel} class="pf-m-secondary">
                    ${this.cancelText}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-modal": ModalForm;
    }
}
