import { PreventFormSubmit } from "@goauthentik/app/elements/forms/helpers";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { MessageLevel } from "@goauthentik/common/messages";
import { camelToSnake, convertToSlug } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError, ValidationError, ValidationErrorFromJSON } from "@goauthentik/api";

export class APIError extends Error {
    constructor(public response: ValidationError) {
        super();
    }
}

export interface KeyUnknown {
    [key: string]: unknown;
}

/**
 * Form
 *
 * The base form element for interacting with user inputs.
 *
 * All forms either[1] inherit from this class and implement the `renderForm()` method to
 * produce the actual form, or include the form in-line as a slotted element. Bizarrely, this form
 * will not render at all if it's not actually in the viewport?[2]
 *
 * @element ak-form
 *
 * @slot - Where the form goes if `renderForm()` returns undefined.
 * @fires eventname - description
 *
 * @csspart partname - description
 */

/* TODO:
 *
 * 1. Specialization: Separate this component into three different classes:
 *    - The base class
 *    - The "use `renderForm` class
 *    - The slotted class.
 * 2. There is already specialization-by-type throughout all of our code.
 *    Consider refactoring serializeForm() so that the conversions are on
 *    the input types, rather than here. (i.e. "Polymorphism is better than
 *    switch.")
 *
 *
 */

@customElement("ak-form")
export abstract class Form<T> extends AKElement {
    abstract send(data: T): Promise<unknown>;

    viewportCheck = true;

    @property()
    successMessage = "";

    @state()
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
            PFSwitch,
            css`
                select[multiple] {
                    height: 15em;
                }
            `,
        ];
    }

    /**
     * Called by the render function. Blocks rendering the form if the form is not within the
     * viewport.
     */
    get isInViewport(): boolean {
        const rect = this.getBoundingClientRect();
        return !(rect.x + rect.y + rect.width + rect.height === 0);
    }

    getSuccessMessage(): string {
        return this.successMessage;
    }

    /**
     * After rendering the form, if there is both a `name` and `slug` element within the form,
     * events the `name` element so that the slug will always have a slugified version of the
     * `name.`. This duplicates functionality within ak-form-element-horizontal.
     */
    updated(): void {
        this.shadowRoot
            ?.querySelectorAll("ak-form-element-horizontal[name=name]")
            .forEach((nameInput) => {
                const input = nameInput.firstElementChild as HTMLInputElement;
                const form = nameInput.closest("form");
                if (form === null) {
                    return;
                }
                const slugFieldWrapper = form.querySelector(
                    "ak-form-element-horizontal[name=slug]",
                );
                if (!slugFieldWrapper) {
                    return;
                }
                const slugField = slugFieldWrapper.firstElementChild as HTMLInputElement;
                // Only attach handler if the slug is already equal to the name
                // if not, they are probably completely different and shouldn't update
                // each other
                if (convertToSlug(input.value) !== slugField.value) {
                    return;
                }
                nameInput.addEventListener("input", () => {
                    slugField.value = convertToSlug(input.value);
                });
            });
    }

    resetForm(): void {
        const form = this.shadowRoot?.querySelector<HTMLFormElement>("form");
        form?.reset();
    }

    /**
     * Return the form elements that may contain filenames. Not sure why this is quite so
     * convoluted. There is exactly one case where this is used:
     * `./flow/stages/prompt/PromptStage: 147: case PromptTypeEnum.File.`
     * Consider moving this functionality to there.
     */
    getFormFiles(): { [key: string]: File } {
        const files: { [key: string]: File } = {};
        const elements =
            this.shadowRoot?.querySelectorAll<HorizontalFormElement>(
                "ak-form-element-horizontal",
            ) || [];
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            element.requestUpdate();
            const inputElement = element.querySelector<HTMLInputElement>("[name]");
            if (!inputElement) {
                continue;
            }
            if (inputElement.tagName.toLowerCase() === "input" && inputElement.type === "file") {
                if ((inputElement.files || []).length < 1) {
                    continue;
                }
                files[element.name] = (inputElement.files || [])[0];
            }
        }
        return files;
    }

    /**
     * Convert the elements of the form to JSON.[4]
     *
     */
    serializeForm(): T | undefined {
        const elements =
            this.shadowRoot?.querySelectorAll<HorizontalFormElement>(
                "ak-form-element-horizontal",
            ) || [];
        const json: { [key: string]: unknown } = {};
        elements.forEach((element) => {
            element.requestUpdate();
            const inputElement = element.querySelector<HTMLInputElement>("[name]");
            if (element.hidden || !inputElement) {
                return;
            }
            // Skip elements that are writeOnly where the user hasn't clicked on the value
            if (element.writeOnly && !element.writeOnlyActivated) {
                return;
            }
            if (
                inputElement.tagName.toLowerCase() === "select" &&
                "multiple" in inputElement.attributes
            ) {
                const selectElement = inputElement as unknown as HTMLSelectElement;
                this.assignValue(
                    inputElement,
                    Array.from(selectElement.selectedOptions).map((v) => v.value),
                    json,
                );
            } else if (
                inputElement.tagName.toLowerCase() === "input" &&
                inputElement.type === "date"
            ) {
                this.assignValue(inputElement, inputElement.valueAsDate, json);
            } else if (
                inputElement.tagName.toLowerCase() === "input" &&
                inputElement.type === "datetime-local"
            ) {
                this.assignValue(inputElement, new Date(inputElement.valueAsNumber), json);
            } else if (
                inputElement.tagName.toLowerCase() === "input" &&
                "type" in inputElement.dataset &&
                inputElement.dataset["type"] === "datetime-local"
            ) {
                // Workaround for Firefox <93, since 92 and older don't support
                // datetime-local fields
                this.assignValue(inputElement, new Date(inputElement.value), json);
            } else if (
                inputElement.tagName.toLowerCase() === "input" &&
                inputElement.type === "checkbox"
            ) {
                this.assignValue(inputElement, inputElement.checked, json);
            } else if ("selectedFlow" in inputElement) {
                this.assignValue(inputElement, inputElement.value, json);
            } else if (inputElement.tagName.toLowerCase() === "ak-search-select") {
                const select = inputElement as unknown as SearchSelect<unknown>;
                try {
                    const value = select.toForm();
                    this.assignValue(inputElement, value, json);
                } catch (exc) {
                    if (exc instanceof PreventFormSubmit) {
                        throw new PreventFormSubmit(exc.message, element);
                    }
                    throw exc;
                }
            } else {
                this.assignValue(inputElement, inputElement.value, json);
            }
        });
        return json as unknown as T;
    }

    /**
     * Recursively assign `value` into `json` while interpreting the dot-path of `element.name`
     */
    private assignValue(
        element: HTMLInputElement,
        value: unknown,
        json: { [key: string]: unknown },
    ): void {
        let parent = json;
        if (!element.name?.includes(".")) {
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

    /**
     * Serialize and send the form to the destination. The `send()` method must be overridden for
     * this to work. If processing the data results in an error, we catch the error, distribute
     * field-levels errors to the fields, and send the rest of them to the Notifications.
     *
     */
    async submit(ev: Event): Promise<unknown | undefined> {
        ev.preventDefault();
        try {
            const data = this.serializeForm();
            if (!data) {
                return;
            }
            const response = await this.send(data);
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
            return response;
        } catch (ex) {
            if (ex instanceof ResponseError) {
                let msg = ex.response.statusText;
                if (ex.response.status > 399 && ex.response.status < 500) {
                    const errorMessage = ValidationErrorFromJSON(await ex.response.json());
                    if (!errorMessage) return errorMessage;
                    if (errorMessage instanceof Error) {
                        throw errorMessage;
                    }
                    // assign all input-related errors to their elements
                    const elements =
                        this.shadowRoot?.querySelectorAll<HorizontalFormElement>(
                            "ak-form-element-horizontal",
                        ) || [];
                    elements.forEach((element) => {
                        element.requestUpdate();
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
                    if (errorMessage.nonFieldErrors) {
                        this.nonFieldErrors = errorMessage.nonFieldErrors;
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
            }
            if (ex instanceof PreventFormSubmit && ex.element) {
                ex.element.errorMessages = [ex.message];
                ex.element.invalid = true;
            }
            // rethrow the error so the form doesn't close
            throw ex;
        }
    }

    renderFormWrapper(): TemplateResult {
        const inline = this.renderForm();
        if (inline) {
            return html`<form
                class="pf-c-form pf-m-horizontal"
                @submit=${(ev: Event) => {
                    ev.preventDefault();
                }}
            >
                ${inline}
            </form>`;
        }
        return html`<slot></slot>`;
    }

    renderForm(): TemplateResult | undefined {
        return undefined;
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
        return html` ${this.renderNonFieldErrors()} ${this.renderFormWrapper()}`;
    }

    render(): TemplateResult {
        if (this.viewportCheck && !this.isInViewport) {
            return html``;
        }
        return this.renderVisible();
    }
}
