import "#elements/LoadingOverlay";

import { isFormField } from "./form-associated-element";

import { EVENT_REFRESH } from "#common/constants";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { APIMessage, MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import { reportInvalidFields } from "#elements/forms/errors";
import { reportValidityDeep } from "#elements/forms/FormGroup";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";
import { serializeForm } from "#elements/forms/serialization";
import { showMessage } from "#elements/messages/MessageContainer";
import { TransclusionElement } from "#elements/modals/shared";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";
import { createFileMap } from "#elements/utils/inputs";

import { ConsoleLogger } from "#logger/browser";

import { instanceOfValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFSwitch from "@patternfly/patternfly/components/Switch/switch.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

//#region Form

/**
 * A helper type, used for typing the submit event of forms that extends this base class.
 */
export interface AKFormSubmitEvent<T> extends SubmitEvent {
    target: Form<T>;
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
 * @class Form
 *
 * @slot - Where the form goes if `renderForm()` returns undefined.
 * @fires ak-refresh - Dispatched when the form has been successfully submitted and data has changed.
 * @fires ak-submitted - Dispatched when the form is submitted.
 * @fires submit - The native submit event, re-dispatched after a successful submission for parent components to listen for.
 * @csspart partname - description
 *
 *
 * @template T - The type of the form data to be sent. Must be serializable by `serializeForm()`.
 * @template D - The type of the data returned by the `send()` method. Defaults to the same as `T`. *
 *
 * @remarks
 * TODO:
 *
 * 1. Specialization: Separate this component into three different classes:
 *    - The base class
 *    - The "use `renderForm` class
 *    - The slotted class.
 * 2. There is already specialization-by-type throughout all of our code.
 *    Consider refactoring serializeForm() so that the conversions are on
 *    the input types, rather than here. (i.e. "Polymorphism is better than
 *    switch.")
 */
@customElement("ak-form")
export class Form<T = Record<string, unknown>, D = T>
    extends AKElement
    implements TransclusionElement
{
    public static styles: CSSResult[] = [
        PFCard,
        PFButton,
        PFForm,
        PFAlert,
        PFInputGroup,
        PFFormControl,
        PFSwitch,
        PFTitle,
        css`
            select[multiple] {
                height: 15em;
            }
        `,
    ];

    /**
     * A helper method to create an invoker for a modal containing this form.
     *
     * ```ts
     * class AKUserListPage extends TablePage<User> {
     *   #openUserModal = UserForm.asModalInvoker();
     * }
     *```
     *
     * @see {@linkcode asInvoker} for the underlying implementation.
     */
    public static asModalInvoker() {
        return asInvoker(this as unknown as CustomElementConstructor);
    }

    protected logger = ConsoleLogger.prefix(`form/${this.tagName.toLowerCase()}`);

    /**
     * Send the serialized form to its destination.
     *
     * @param data The serialized form data.
     * @returns A promise that resolves when the data has been sent.
     * @abstract
     */
    protected send?(data: NonNullable<D>): Promise<unknown>;

    viewportCheck = true;

    //#region Properties

    @property({ type: String })
    public successMessage?: string;

    @property({ type: String })
    public autocomplete?: Exclude<AutoFillBase, "">;

    @property({ type: String, useDefault: true })
    public headline?: string | null = null;

    @property({ type: String, attribute: "action-label", useDefault: true })
    public actionLabel: string | null = null;

    //#endregion

    public get form(): HTMLFormElement | null {
        return this.renderRoot?.querySelector("form") || null;
    }

    @state()
    protected loading = false;

    protected loadingOverlay = this.ownerDocument.createElement("ak-loading-overlay");

    @state()
    protected nonFieldErrors: readonly string[] | null = null;

    /**
     * Optiona singular label for the type of entity this form creates/edits, used in success messages and the like.
     */
    protected entitySingular?: string;
    /**
     * Optiona plural label for the type of entity this form creates/edits, used in success messages and the like.
     */
    protected entityPlural?: string;

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

    protected defaultSlot: HTMLSlotElement = this.ownerDocument.createElement("slot");

    /**
     * An overridable method for returning a success message after a successful submission.
     *
     * @deprecated Use `formatAPISuccessMessage` instead.
     */
    public getSuccessMessage(): string | undefined {
        return this.successMessage;
    }

    /**
     * An overridable method for returning a formatted message after a successful submission.
     */
    protected formatAPISuccessMessage(_response: unknown): APIMessage | null {
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

    /**
     * An overridable method for formatting the form headline.
     */
    protected formatHeadline(headline = this.headline): string {
        return headline || "";
    }

    /**
     * An overridable method for formatting the submit button label.
     */
    protected formatSubmitLabel(actionLabel = this.actionLabel): string {
        return actionLabel || msg("Submit");
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
            this.logger.warn("Unable to check validity, no form found", this);
            return false;
        }

        return reportValidityDeep(form);
    }

    //#endregion

    //#region Submission

    /**
     * Convert the elements of the form to JSON.[4]
     */
    public toJSON(): D {
        const elements = this.renderRoot.querySelectorAll("ak-form-element-horizontal");

        if (elements.length) {
            return serializeForm<D>(elements);
        }

        const assignedElements = this.defaultSlot.assignedElements({ flatten: true });

        const [firstAssignedElement] = assignedElements;

        if (assignedElements.length === 1 && isFormField(firstAssignedElement)) {
            return firstAssignedElement.toJSON() as D;
        }

        const namedElements = assignedElements.filter((element): element is AKElement => {
            return element.hasAttribute("name");
        });

        if (namedElements.length) {
            return serializeForm<D>(namedElements);
        }

        return {} as D;
    }

    /**
     * Serialize and send the form to the destination. The `send()` method must be overridden for
     * this to work. If processing the data results in an error, we catch the error, distribute
     * field-levels errors to the fields, and send the rest of them to the Notifications.
     */
    public submit = (submitEvent: SubmitEvent): Promise<unknown | false> => {
        submitEvent.preventDefault();

        let data: D;

        try {
            data = this.toJSON();
        } catch (error) {
            this.logger.error("An error occurred while serializing the form.", error);

            showMessage({
                level: MessageLevel.error,
                message: msg("An unknown error occurred while submitting the form."),
                description: pluckErrorDetail(error),
            });

            return Promise.resolve(false);
        }

        if (!data) return Promise.resolve(false);

        if (!this.send) {
            this.logger.info("No send() method implemented on form, dispatching submit event");
            this.dispatchEvent(submitEvent);
            return Promise.resolve(false);
        }

        return this.send(data)
            .then((response) => {
                showMessage(this.formatAPISuccessMessage(response));

                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );

                // Re-dispatch the submit event so that parent components can listen for it.
                this.dispatchEvent(submitEvent);

                return response;
            })
            .catch(async (error: unknown) => {
                if (
                    error instanceof PreventFormSubmit &&
                    error.element instanceof HorizontalFormElement
                ) {
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

                        this.logger.error(
                            "API rejected the form submission due to an invalid field that doesn't appear to be in the form. This is likely a bug in authentik.",
                            parsedError,
                        );
                    }
                }

                showMessage(this.formatAPIErrorMessage(parsedError), true);

                // Rethrow the error so the form doesn't close.
                throw error;
            });
    };

    protected doSubmit = (event: SubmitEvent): void => {
        if (this.loading) {
            this.logger.info("Skipping submit. Already submitting!");
        }

        this.loading = true;

        this.submit(event).finally(() => {
            this.loading = false;
        });
    };

    //#endregion

    //#endregion

    //#region Render

    protected renderFormWrapper(): SlottedTemplateResult {
        const inline = this.renderForm();

        if (!inline) {
            return this.defaultSlot;
        }

        return html`<form
            id="form"
            class="pf-c-form pf-m-horizontal"
            autocomplete=${ifDefined(this.autocomplete)}
            method="dialog"
            @submit=${this.doSubmit}
        >
            ${inline}
        </form>`;
    }

    /**
     * An overridable method for rendering the form content.
     */
    protected renderForm(): SlottedTemplateResult | null {
        return null;
    }

    /**
     * Render errors that are not associated with a specific field.
     */
    protected renderNonFieldErrors(): SlottedTemplateResult {
        return guard([this.nonFieldErrors], () => {
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
        });
    }

    /**
     * An overridable method for rendering the form header.
     *
     * @remarks
     * If this form is slotted, such as in a modal, this method will not render anything,
     * allowing the slot parent to provide the header in a more visually appropriate manner.
     */
    public renderHeader(force?: boolean): SlottedTemplateResult {
        const { assignedSlot, headline } = this;

        return guard([force, assignedSlot, headline], () => {
            if (!force && assignedSlot && (!assignedSlot.name || assignedSlot.name === "form")) {
                return nothing;
            }

            return this.formatHeadline(headline);
        });
    }

    /**
     * An overridable method for rendering the form actions.
     *
     * @remarks
     * If this form is slotted, such as in a modal, this method will not render anything,
     * allowing the slot parent to provide the actions in a more visually appropriate manner.
     */
    public renderActions(force?: boolean): SlottedTemplateResult {
        const { assignedSlot, actionLabel } = this;

        return guard([force, assignedSlot, actionLabel], () => {
            if (!force && assignedSlot && (!assignedSlot.name || assignedSlot.name === "form")) {
                return nothing;
            }

            return html`<fieldset part="form-actions" class="pf-c-card__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <button
                    type="button"
                    class="pf-c-button pf-m-primary"
                    @click=${() => {
                        this.doSubmit(
                            new SubmitEvent("submit", {
                                submitter: this,
                                cancelable: true,
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    }}
                    part="submit-button"
                    aria-description=${msg("Submit action")}
                >
                    ${this.formatSubmitLabel(actionLabel)}
                </button>
            </fieldset>`;
        });
    }

    /**
     * An overridable method for rendering the form when it is visible.
     */
    protected renderVisible(): SlottedTemplateResult {
        return [
            this.loading ? this.loadingOverlay : nothing,
            this.renderHeader(),
            this.renderNonFieldErrors(),
            this.renderFormWrapper(),
            this.renderActions(),
        ];
    }

    protected override render(): SlottedTemplateResult {
        if (this.viewportCheck && !this.isInViewport) {
            return nothing;
        }

        return this.renderVisible();
    }

    //#endregion
}
