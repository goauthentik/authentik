import "@polymer/iron-form/iron-form";
import { IronFormElement } from "@polymer/iron-form/iron-form";
import "@polymer/paper-input/paper-input";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError, ValidationError } from "@goauthentik/api";

import { EVENT_REFRESH } from "../../constants";
import { showMessage } from "../../elements/messages/MessageContainer";
import { camelToSnake, convertToSlug } from "../../utils";
import { SearchSelect } from "../SearchSelect";
import { MessageLevel } from "../messages/Message";
import { HorizontalFormElement } from "./HorizontalFormElement";

export class APIError extends Error {
    constructor(public response: ValidationError) {
        super();
    }
}

@customElement("ak-form")
export class Form<T> extends LitElement {
    viewportCheck = true;

    @property()
    successMessage = "";

    @property()
    send!: (data: T) => Promise<unknown>;

    @property({ attribute: false })
    nonFieldErrors?: string[];

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFCard,
            PFButton,
            PFForm,
            PFAlert,
            PFInputGroup,
            PFFormControl,
            AKGlobal,
            css`
                select[multiple] {
                    height: 15em;
                }
            `,
        ];
    }

    get isInViewport(): boolean {
        const rect = this.getBoundingClientRect();
        return !(rect.x + rect.y + rect.width + rect.height === 0);
    }

    getSuccessMessage(): string {
        return this.successMessage;
    }

    updated(): void {
        this.shadowRoot
            ?.querySelectorAll<HTMLInputElement>("input[name=name]")
            .forEach((nameInput) => {
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
    resetForm(): void {
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        ironForm?.reset();
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
        elements.forEach((element) => {
            const values = form._serializeElementValues(element);
            if (element.hidden) {
                return;
            }
            if (element.tagName.toLowerCase() === "select" && "multiple" in element.attributes) {
                json[element.name] = values;
            } else if (element.tagName.toLowerCase() === "input" && element.type === "date") {
                json[element.name] = element.valueAsDate;
            } else if (
                element.tagName.toLowerCase() === "input" &&
                element.type === "datetime-local"
            ) {
                json[element.name] = new Date(element.valueAsNumber);
            } else if (
                element.tagName.toLowerCase() === "input" &&
                "type" in element.dataset &&
                element.dataset["type"] === "datetime-local"
            ) {
                // Workaround for Firefox <93, since 92 and older don't support
                // datetime-local fields
                json[element.name] = new Date(element.value);
            } else if (element.tagName.toLowerCase() === "input" && element.type === "checkbox") {
                json[element.name] = element.checked;
            } else if (element.tagName.toLowerCase() === "ak-search-select") {
                const select = element as unknown as SearchSelect<unknown>;
                try {
                    json[element.name] = select.value(select.selectedObject);
                } catch {
                    console.debug("authentik/form: SearchSelect.value error");
                }
            } else {
                for (let v = 0; v < values.length; v++) {
                    this.serializeFieldRecursive(element, values[v], json);
                }
            }
        });
        return json as unknown as T;
    }

    private serializeFieldRecursive(
        element: HTMLInputElement,
        value: unknown,
        json: { [key: string]: unknown },
    ): void {
        let parent = json;
        if (!element.name.includes(".")) {
            parent[element.name] = value;
            return;
        }
        const nameElements = element.name.split(".");
        for (let index = 0; index < nameElements.length - 1; index++) {
            const nameEl = nameElements[index];
            // Ensure all nested structures exist
            if (!(nameEl in parent)) parent[nameEl] = {};
            parent = parent[nameEl] as { [key: string]: unknown };
        }
        parent[nameElements[nameElements.length - 1]] = value;
    }

    submit(ev: Event): Promise<unknown> | undefined {
        ev.preventDefault();
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            console.warn("authentik/forms: failed to find iron-form");
            return;
        }
        const data = this.serializeForm(ironForm);
        return this.send(data)
            .then((r) => {
                showMessage({
                    level: MessageLevel.success,
                    message: this.getSuccessMessage(),
                });
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
                return r;
            })
            .catch(async (ex: Error | ResponseError) => {
                if (!(ex instanceof ResponseError)) {
                    throw ex;
                }
                let msg = ex.response.statusText;
                if (ex.response.status > 399 && ex.response.status < 500) {
                    const errorMessage: ValidationError = await ex.response.json();
                    if (!errorMessage) return errorMessage;
                    if (errorMessage instanceof Error) {
                        throw errorMessage;
                    }
                    // assign all input-related errors to their elements
                    const elements: HorizontalFormElement[] = ironForm._getSubmittableElements();
                    elements.forEach((element) => {
                        const elementName = element.name;
                        if (!elementName) return;
                        if (camelToSnake(elementName) in errorMessage) {
                            element.errorMessages = errorMessage[camelToSnake(elementName)];
                            element.invalid = true;
                        } else {
                            element.errorMessages = [];
                            element.invalid = false;
                        }
                    });
                    if ("non_field_errors" in errorMessage) {
                        this.nonFieldErrors = errorMessage["non_field_errors"];
                    }
                    // Only change the message when we have `detail`.
                    // Everything else is handled in the form.
                    if ("detail" in errorMessage) {
                        msg = errorMessage.detail;
                    }
                }
                // error is local or not from rest_framework
                showMessage({
                    message: msg,
                    level: MessageLevel.error,
                });
                // rethrow the error so the form doesn't close
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
            ${this.nonFieldErrors.map((err) => {
                return html`<div class="pf-c-alert pf-m-inline pf-m-danger">
                    <div class="pf-c-alert__icon">
                        <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <h4 class="pf-c-alert__title">${err}</h4>
                </div>`;
            })}
        </div>`;
    }

    renderVisible(): TemplateResult {
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => {
                this.submit(ev);
            }}
        >
            ${this.renderNonFieldErrors()} ${this.renderForm()}
        </iron-form>`;
    }

    render(): TemplateResult {
        if (this.viewportCheck && !this.isInViewport) {
            return html``;
        }
        return this.renderVisible();
    }
}
