import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { EVENT_REFRESH } from "../../constants";
import { ModalButton } from "../buttons/ModalButton";
import { Form } from "./Form";
import "../buttons/SpinnerButton";

@customElement("ak-forms-modal")
export class ModalForm extends ModalButton {

    @property({ type: Boolean })
    closeAfterSuccessfulSubmit = true;

    confirm(): Promise<void>  {
        const form = this.querySelector<Form<unknown>>("[slot=form]");
        if (!form) {
            return Promise.reject(t`No form found`);
        }
        const formPromise = form.submit(new Event("submit"));
        if (!formPromise) {
            return Promise.reject(t`Form didn't return a promise for submitting`);
        }
        return formPromise.then(() => {
            if (this.closeAfterSuccessfulSubmit) {
                this.open = false;
                form?.resetForm();
            }
            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                })
            );
        });
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1 class="pf-c-title pf-m-2xl">
                    <slot name="header"></slot>
                </h1>
            </div>
        </section>
        <section class="pf-c-page__main-section pf-m-light">
            <slot name="form"></slot>
        </section>
        <footer class="pf-c-modal-box__footer">
            <ak-spinner-button
                .callAction=${() => {
                    return this.confirm();
                }}
                class="pf-m-primary">
                <slot name="submit"></slot>
            </ak-spinner-button>&nbsp;
            <ak-spinner-button
                .callAction=${async () => {
                    this.resetForms();
                    this.open = false;
                }}
                class="pf-m-secondary">
                ${t`Cancel`}
            </ak-spinner-button>
        </footer>`;
    }

}
