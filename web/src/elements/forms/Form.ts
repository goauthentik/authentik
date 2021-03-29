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
import { IronFormElement } from "@polymer/iron-form/iron-form";
import { camelToSnake } from "../../utils";
import { ValidationError } from "authentik-api/src";

export class APIError extends Error {

    constructor(public response: ValidationError) {
        super();
    }

}

@customElement("ak-form")
export class Form<T> extends LitElement {

    @property()
    successMessage = "";

    @property()
    send!: (data: T) => Promise<unknown>;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFFormControl, AKGlobal, css`
            select[multiple] {
                height: 15em;
            }
        `];
    }

    getSuccessMessage(): string {
        return this.successMessage;
    }

    serializeForm(form: IronFormElement): T {
        const elements = form._getSubmittableElements();
        const json: { [key: string]: unknown } = {};
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i] as HTMLInputElement;
            const values = form._serializeElementValues(element);
            if (element.tagName.toLowerCase() === "select" && "multiple" in element.attributes) {
                json[element.name] = values;
            } else {
                for (let v = 0; v < values.length; v++) {
                    form._addSerializedElement(json, element.name, values[v]);
                }
            }
        }
        return json as unknown as T;
    }

    submit(ev: Event): Promise<unknown> | undefined {
        ev.preventDefault();
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            console.warn("authentik/forms: failed to find iron-form");
            return;
        }
        const data = this.serializeForm(ironForm);
        return this.send(data).then((r) => {
            showMessage({
                level: MessageLevel.success,
                message: this.getSuccessMessage()
            });
            return r;
        }).catch((ex: Response) => {
            if (ex.status > 399 && ex.status < 500) {
                return ex.json().then((errorMessage: ValidationError) => {
                    if (!errorMessage) return errorMessage;
                    if (errorMessage instanceof Error) {
                        throw errorMessage;
                    }
                    const elements: PaperInputElement[] = ironForm._getSubmittableElements();
                    elements.forEach((element) => {
                        const elementName = element.name;
                        if (!elementName) return;
                        if (camelToSnake(elementName) in errorMessage) {
                            element.errorMessage = errorMessage[camelToSnake(elementName)].join(", ");
                            element.invalid = true;
                        }
                    });
                    throw new APIError(errorMessage);
                });
            }
            throw ex;
        });
    }

    renderForm(): TemplateResult {
        return html`<slot></slot>`;
    }

    render(): TemplateResult {
        const rect = this.getBoundingClientRect();
        if (rect.x + rect.y + rect.width + rect.height === 0) {
            return html``;
        }
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => { this.submit(ev); }}>
            ${this.renderForm()}
        </iron-form>`;
    }

}
