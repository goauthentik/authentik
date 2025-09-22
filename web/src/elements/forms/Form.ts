import { EVENT_REFRESH } from "#common/constants";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { dateToUTC } from "#common/temporal";

import { isControlElement } from "#elements/AkControlElement";
import { AKElement } from "#elements/Base";
import { reportValidityDeep } from "#elements/forms/FormGroup";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";
import { APIMessage } from "#elements/messages/Message";
import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { createFileMap, isNamedElement, NamedElement } from "#elements/utils/inputs";

import { ErrorProp } from "#components/ak-field-errors";

import { instanceOfValidationError, ValidationError } from "@goauthentik/api";

import { snakeCase } from "change-case";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

function isIgnored<T extends Element>(element: T) {
    if (!(element instanceof HTMLElement)) return false;

    return element.dataset.formIgnore === "true";
}

/**
 * Recursively assign `value` into `json` while interpreting the dot-path of `element.name`
 */
function assignValue(
    element: NamedElement,
    value: unknown,
    destination: Record<string, unknown>,
): void {
    let parent = destination;

    if (!element.name?.includes(".")) {
        parent[element.name] = value;
        return;
    }

    const nameElements = element.name.split(".");

    for (let index = 0; index < nameElements.length - 1; index++) {
        const nameEl = nameElements[index];
        // Ensure all nested structures exist
        if (!(nameEl in parent)) {
            parent[nameEl] = {};
        }
        parent = parent[nameEl] as { [key: string]: unknown };
    }

    parent[nameElements[nameElements.length - 1]] = value;
}

/**
 * Convert the elements of the form to JSON.[4]
 *
 */
export function serializeForm<T = Record<string, unknown>>(elements: Iterable<AKElement>): T {
    const json: Record<string, unknown> = {};

    Array.from(elements).forEach((element) => {
        element.requestUpdate();

        if (element.hidden) return;

        if (isNamedElement(element) && isControlElement(element)) {
            return assignValue(element, element.json(), json);
        }

        const inputElement = element.querySelector("[name]");

        if (element.hidden || !inputElement || isIgnored(inputElement)) {
            return;
        }

        if (isNamedElement(element) && isControlElement(inputElement)) {
            return assignValue(element, inputElement.json(), json);
        }

        if (inputElement instanceof HTMLSelectElement && inputElement.multiple) {
            const selectElement = inputElement as unknown as HTMLSelectElement;

            return assignValue(
                inputElement,
                Array.from(selectElement.selectedOptions, (v) => v.value),
                json,
            );
        }

        if (inputElement instanceof HTMLInputElement) {
            if (inputElement.type === "date") {
                return assignValue(inputElement, inputElement.valueAsDate, json);
            }

            if (inputElement.type === "datetime-local") {
                return assignValue(
                    inputElement,
                    dateToUTC(new Date(inputElement.valueAsNumber)),
                    json,
                );
            }

            if ("type" in inputElement.dataset && inputElement.dataset.type === "datetime-local") {
                // Workaround for Firefox <93, since 92 and older don't support
                // datetime-local fields
                return assignValue(inputElement, dateToUTC(new Date(inputElement.value)), json);
            }

            if (inputElement.type === "checkbox") {
                return assignValue(inputElement, inputElement.checked, json);
            }
        }

        if (isNamedElement(inputElement) && "value" in inputElement) {
            return assignValue(inputElement, inputElement.value, json);
        }

        console.error(`authentik/forms: Could not find value for element`, {
            element,
            inputElement,
            json,
        });

        throw new Error(`Could not find value for element ${inputElement.tagName}`);
    });

    return json as unknown as T;
}

//#region Validation Reporting

/**
 * Assign all input-related errors to their respective elements.
 */
function reportInvalidFields(
    parsedError: ValidationError,
    elements: Iterable<HorizontalFormElement>,
): HorizontalFormElement[] {
    const invalidFields: HorizontalFormElement[] = [];

    for (const element of elements) {
        element.requestUpdate();

        const elementName = element.name;

        if (!elementName) continue;

        const snakeProperty = snakeCase(elementName);
        const errorMessages: ErrorProp[] = parsedError[snakeProperty] ?? [];

        element.errorMessages = errorMessages;

        if (Array.isArray(errorMessages) && errorMessages.length) {
            invalidFields.push(element);
        }
    }

    return invalidFields;
}

//#endregion

//#region Form

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
export abstract class Form<T = Record<string, unknown>> extends AKElement {
    abstract send(data: T): Promise<unknown>;

    viewportCheck = true;

    //#region Properties

    @property({ type: String })
    public successMessage?: string;

    @property({ type: String })
    public autocomplete?: AutoFill;

    //#endregion

    public get form(): HTMLFormElement | null {
        return this.renderRoot?.querySelector("form") || null;
    }

    @state()
    nonFieldErrors?: string[];

    static styles: CSSResult[] = [
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

    /**
     * Called by the render function.
     *
     * Blocks rendering the form if the form is not within the
     * viewport.
     *
     * @todo Consider using a observer instead.
     */
    public get isInViewport(): boolean {
        const rect = this.getBoundingClientRect();
        return rect.x + rect.y + rect.width + rect.height !== 0;
    }

    /**
     * An overridable method for returning a success message after a successful submission.
     *
     * @deprecated Use `formatAPISuccessMessage` instead.
     */
    protected getSuccessMessage(): string | undefined {
        return this.successMessage;
    }

    /**
     * An overridable method for returning a formatted message after a successful submission.
     */
    protected formatAPISuccessMessage(response: unknown): APIMessage | null {
        const message = this.getSuccessMessage();

        if (!message) return null;

        return {
            level: MessageLevel.success,
            message,
        };
    }

    /**
     * An overridable method for returning a formatted error message after a failed submission.
     */
    protected formatAPIErrorMessage(error: APIError): APIMessage | null {
        return {
            message: msg("There was an error submitting the form."),
            description: pluckErrorDetail(error, pluckFallbackFieldErrors(error)[0]),
            level: MessageLevel.error,
        };
    }

    //#region Public methods

    public reset(): void {
        const form = this.shadowRoot?.querySelector("form");

        return form?.reset();
    }

    /**
     * Return the form elements that may contain filenames.
     */
    public files<T extends PropertyKey = PropertyKey>(): Map<T, File> {
        return createFileMap<T>(this.shadowRoot?.querySelectorAll("ak-form-element-horizontal"));
    }

    //#region Validation

    public checkValidity(): boolean {
        return !!this.form?.checkValidity?.();
    }

    public reportValidity(): boolean {
        const form = this.form;

        if (!form) {
            console.warn("authentik/forms: unable to check validity, no form found", this);
            return false;
        }

        return reportValidityDeep(form);
    }

    //#endregion

    //#region Submission

    /**
     * Convert the elements of the form to JSON.[4]
     */
    protected serialize(): T | undefined {
        const elements = this.shadowRoot?.querySelectorAll("ak-form-element-horizontal");

        if (!elements) {
            return {} as T;
        }

        return serializeForm<T>(elements);
    }

    /**
     * Serialize and send the form to the destination. The `send()` method must be overridden for
     * this to work. If processing the data results in an error, we catch the error, distribute
     * field-levels errors to the fields, and send the rest of them to the Notifications.
     */
    public submit(event: SubmitEvent): Promise<unknown | false> {
        event.preventDefault();

        const data = this.serialize();

        if (!data) return Promise.resolve(false);

        return this.send(data)
            .then((response) => {
                showMessage(this.formatAPISuccessMessage(response));

                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );

                return response;
            })
            .catch(async (error: unknown) => {
                if (error instanceof PreventFormSubmit && error.element) {
                    error.element.errorMessages = [error.message];
                }

                const parsedError = await parseAPIResponseError(error);

                if (instanceOfValidationError(parsedError)) {
                    const invalidFields = reportInvalidFields(
                        parsedError,
                        this.renderRoot.querySelectorAll("ak-form-element-horizontal"),
                    );

                    const focusTarget = Iterator.from(invalidFields)
                        .map(({ focusTarget }) => focusTarget)
                        .find(Boolean);

                    if (focusTarget) {
                        requestAnimationFrame(() => focusTarget.focus());
                    } else if (Array.isArray(parsedError.nonFieldErrors)) {
                        this.nonFieldErrors = parsedError.nonFieldErrors;
                    } else {
                        this.nonFieldErrors = pluckFallbackFieldErrors(parsedError);

                        console.error(
                            "authentik/forms: API rejected the form submission due to an invalid field that doesn't appear to be in the form. This is likely a bug in authentik.",
                            parsedError,
                        );
                    }
                }

                showMessage(this.formatAPIErrorMessage(parsedError), true);

                // Rethrow the error so the form doesn't close.
                throw error;
            });
    }

    //#endregion

    //#endregion

    //#region Render

    public renderFormWrapper(): TemplateResult {
        const inline = this.renderForm();

        if (!inline) {
            return html`<slot></slot>`;
        }

        return html`<form
            class="pf-c-form pf-m-horizontal"
            autocomplete=${ifDefined(this.autocomplete)}
            @submit=${(event: SubmitEvent) => {
                event.preventDefault();
            }}
        >
            ${inline}
        </form>`;
    }

    /**
     * An overridable method for rendering the form content.
     */
    public renderForm(): SlottedTemplateResult | null {
        return null;
    }

    public renderNonFieldErrors(): SlottedTemplateResult {
        if (!this.nonFieldErrors) {
            return nothing;
        }

        return html`<div class="pf-c-form__alert">
            ${this.nonFieldErrors.map((err, idx) => {
                return html`<div
                    class="pf-c-alert pf-m-inline pf-m-danger"
                    role="alert"
                    aria-labelledby="error-message-${idx}"
                >
                    <div class="pf-c-alert__icon">
                        <i aria-hidden="true" class="fas fa-exclamation-circle"></i>
                    </div>
                    <p id="error-message-${idx}" class="pf-c-alert__title">${err}</p>
                </div>`;
            })}
        </div>`;
    }

    public renderVisible(): TemplateResult {
        return html` ${this.renderNonFieldErrors()} ${this.renderFormWrapper()}`;
    }

    public render(): SlottedTemplateResult {
        if (this.viewportCheck && !this.isInViewport) {
            return nothing;
        }

        return this.renderVisible();
    }

    //#endregion
}
