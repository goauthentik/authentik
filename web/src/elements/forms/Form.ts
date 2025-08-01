import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { dateToUTC } from "#common/temporal";
import { camelToSnake } from "#common/utils";

import { isControlElement } from "#elements/AkControlElement";
import { AKElement } from "#elements/Base";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";
import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { createFileMap, isNamedElement, NamedElement } from "#elements/utils/inputs";

import { instanceOfValidationError } from "@goauthentik/api";

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

    @property()
    public successMessage = "";

    @property({ type: String })
    public autocomplete?: AutoFill;

    //#endregion

    public get form(): HTMLFormElement | null {
        return this.shadowRoot?.querySelector("form") || null;
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
     */
    protected getSuccessMessage(): string {
        return this.successMessage;
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

    public checkValidity(): boolean {
        return !!this.form?.checkValidity?.();
    }

    public reportValidity(): boolean {
        return !!this.form?.reportValidity?.();
    }

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
            })
            .catch(async (error: unknown) => {
                if (error instanceof PreventFormSubmit && error.element) {
                    error.element.errorMessages = [error.message];
                    error.element.invalid = true;
                }

                const parsedError = await parseAPIResponseError(error);
                let errorMessage = pluckErrorDetail(error);

                if (instanceOfValidationError(parsedError)) {
                    // assign all input-related errors to their elements
                    const elements =
                        this.shadowRoot?.querySelectorAll<HorizontalFormElement>(
                            "ak-form-element-horizontal",
                        ) || [];

                    elements.forEach((element) => {
                        element.requestUpdate();

                        const elementName = element.name;
                        if (!elementName) return;

                        const snakeProperty = camelToSnake(elementName);

                        if (snakeProperty in parsedError) {
                            element.errorMessages = parsedError[snakeProperty];
                            element.invalid = true;
                        } else {
                            element.errorMessages = [];
                            element.invalid = false;
                        }
                    });

                    if (parsedError.nonFieldErrors) {
                        this.nonFieldErrors = parsedError.nonFieldErrors;
                    }

                    errorMessage = msg("Invalid update request.");

                    // Only change the message when we have `detail`.
                    // Everything else is handled in the form.
                    if ("detail" in parsedError) {
                        errorMessage = parsedError.detail;
                    }
                }

                showMessage({
                    message: errorMessage,
                    level: MessageLevel.error,
                });

                // Rethrow the error so the form doesn't close.
                throw error;
            });
    }

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
