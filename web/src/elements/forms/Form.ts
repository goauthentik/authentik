import "@polymer/paper-input/paper-input";
import "@polymer/iron-form/iron-form";
import { PaperInputElement } from "@polymer/paper-input/paper-input";
import { showMessage } from "../../elements/messages/MessageContainer";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import { MessageLevel } from "../messages/Message";

interface ErrorResponse {
    [key: string]: string[];
}

export class APIError extends Error {

    constructor(public response: ErrorResponse) {
        super();
    }

}

@customElement("ak-form")
export class Form<T> extends LitElement {

    @property()
    successMessage = "";

    @property()
    send!: (data: T) => Promise<T>;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFFormControl, AKGlobal, css`
            select[multiple] {
                height: 15em;
            }
        `];
    }

    submit(ev: Event): Promise<T> | undefined {
        ev.preventDefault();
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            console.warn("authentik/forms: failed to find iron-form");
            return;
        }
        const data = ironForm.serializeForm() as T;
        return this.send(data).then((r) => {
            showMessage({
                level: MessageLevel.success,
                message: this.successMessage
            });
            return r;
        }).catch((ex: Response) => {
            if (ex.status > 399 && ex.status < 500) {
                return ex.json();
            }
            return ex;
        }).then((errorMessage: ErrorResponse) => {
            if (!errorMessage) return errorMessage;
            const elements: PaperInputElement[] = ironForm._getSubmittableElements();
            elements.forEach((element) => {
                const elementName = element.name;
                if (!elementName) return;
                if (elementName in errorMessage) {
                    element.errorMessage = errorMessage[elementName].join(", ");
                    element.invalid = true;
                }
            });
            throw new APIError(errorMessage);
        });
    }

    renderForm(): TemplateResult {
        return html`<slot></slot>`;
    }

    render(): TemplateResult {
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => { this.submit(ev); }}>
            ${this.renderForm()}
        </iron-form>`;
    }

}
