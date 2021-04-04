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
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import { MessageLevel } from "../messages/Message";
import { IronFormElement } from "@polymer/iron-form/iron-form";
import { camelToSnake, convertToSlug } from "../../utils";
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

    @property({attribute: false})
    nonFieldErrors?: string[];

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFAlert, PFFormControl, AKGlobal, css`
            select[multiple] {
                height: 15em;
            }
        `];
    }

    getSuccessMessage(): string {
        return this.successMessage;
    }

    updated(): void {
        this.shadowRoot?.querySelectorAll<HTMLInputElement>("input[name=name]").forEach(nameInput => {
            const form = nameInput.closest("form");
            if (form === null) {
                return;
            }
            const slugField = form.querySelector<HTMLInputElement>("input[name=slug]");
            if (!slugField) {
                return;
            }
            // Only attach handler if the slug is already equal to the name
            // if not, they are probably completely different and shouldn't update
            // each other
            if (convertToSlug(nameInput.value) !== slugField.value) {
                return;
            }
            nameInput.addEventListener("input", () => {
                slugField.value = convertToSlug(nameInput.value);
            });
        });
    }

    /**
     * Reset the inner iron-form
     */
    reset(): void {
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            return;
        }
        ironForm.reset();
    }

    /**
     * If this form contains a file input, and the input as been filled, this function returns
     * said file.
     * @returns File object or undefined
     */
    getFormFile(): File | undefined {
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            return;
        }
        const elements = ironForm._getSubmittableElements();
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i] as HTMLInputElement;
            if (element.tagName.toLowerCase() === "input" && element.type === "file") {
                if ((element.files || []).length < 1) {
                    continue;
                }
                // We already checked the length
                return (element.files || [])[0];
            }
        }
    }

    serializeForm(form: IronFormElement): T {
        const elements: HTMLInputElement[] = form._getSubmittableElements();
        const json: { [key: string]: unknown } = {};
        elements.forEach(element => {
            const values = form._serializeElementValues(element);
            if (element.hidden) {
                return;
            }
            if (element.tagName.toLowerCase() === "select" && "multiple" in element.attributes) {
                json[element.name] = values;
            } else if (element.tagName.toLowerCase() === "input" && element.type === "date") {
                json[element.name] = element.valueAsDate;
            } else {
                for (let v = 0; v < values.length; v++) {
                    form._addSerializedElement(json, element.name, values[v]);
                }
            }
        });
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
                    // assign all input-related errors to their elements
                    const elements: PaperInputElement[] = ironForm._getSubmittableElements();
                    elements.forEach((element) => {
                        const elementName = element.name;
                        if (!elementName) return;
                        if (camelToSnake(elementName) in errorMessage) {
                            element.errorMessage = errorMessage[camelToSnake(elementName)].join(", ");
                            element.invalid = true;
                        }
                    });
                    if ("non_field_errors" in errorMessage) {
                        this.nonFieldErrors = errorMessage["non_field_errors"];
                    }
                    throw new APIError(errorMessage);
                });
            }
            throw ex;
        });
    }

    renderForm(): TemplateResult {
        return html`<slot></slot>`;
    }

    renderNonFieldErrors(): TemplateResult {
        if (!this.nonFieldErrors) {
            return html``;
        }
        return html`<div class="pf-c-form__alert">
        ${this.nonFieldErrors.map(err => {
            return html`<div class="pf-c-alert pf-m-inline pf-m-danger">
                <div class="pf-c-alert__icon">
                    <i class="fas fa-exclamation-circle"></i>
                </div>
                <h4 class="pf-c-alert__title">
                    ${err}
                </h4>
            </div>`;
        })}
        </div>`;
    }

    renderVisible(): TemplateResult {
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => { this.submit(ev); }}>
            ${this.renderNonFieldErrors()}
            ${this.renderForm()}
        </iron-form>`;
    }

    render(): TemplateResult {
        const rect = this.getBoundingClientRect();
        if (rect.x + rect.y + rect.width + rect.height === 0) {
            return html``;
        }
        return this.renderVisible();
    }

}
