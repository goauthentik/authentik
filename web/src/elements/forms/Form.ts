import "#elements/LoadingOverlay";

import { isFormField } from "./form-associated-element";

import { EVENT_REFRESH } from "#common/constants";
import { PFSize } from "#common/enums";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { APIMessage, MessageLevel } from "#common/messages";

import { AKElement } from "#elements/Base";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import {
    DialogInit,
    modalInvoker,
    ModalInvokerDirectiveResult,
    renderModal,
} from "#elements/dialogs";
import {
    isTransclusionParentElement,
    TransclusionChildElement,
    TransclusionChildSymbol,
} from "#elements/dialogs/shared";
import { reportInvalidFields } from "#elements/forms/errors";
import Styles from "#elements/forms/Form.css";
import { reportValidityDeep } from "#elements/forms/FormGroup";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";
import { serializeForm } from "#elements/forms/serialization";
import { showMessage } from "#elements/messages/MessageContainer";
import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { createFileMap } from "#elements/utils/inputs";

import { ConsoleLogger } from "#logger/browser";

import { instanceOfValidationError } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { createRef, ref } from "lit-html/directives/ref.js";
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
    implements TransclusionChildElement
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
        Styles,
    ];

    /**
     * Optional singular label for the type of entity this form creates/edits.
     */
    public static verboseName: string | null = null;

    /**
     * Optional plural label for the type of entity this form creates/edits
     */
    public static verboseNamePlural: string | null = null;

    /**
     * The modifier to use in the default headline, e.g. "New"
     */
    public static createLabel: string | null = msg("New", {
        id: "form.new-entity",
    });

    /**
     * The verb to use in the default submit button label, e.g. "Create" or "Update".
     */
    public static submitVerb: string = msg("Create", {
        id: "form.submit.verb.create",
    });

    /**
     * The gerund to use in the message key for the submission message, e.g. "Creating" or "Updating".
     */
    public static submittingVerb: string = msg("Creating", {
        id: "form.submit.verb.creating",
    });

    //#region Modal helpers

    public [TransclusionChildSymbol] = true;

    /**
     * A helper method to create an invoker for a modal containing this form.
     *
     * @see {@linkcode modalInvoker} for the underlying implementation.
     */
    public static asModalInvoker(
        props?: LitPropertyRecord<Form>,
        init?: DialogInit,
    ): ModalInvokerDirectiveResult {
        return modalInvoker(this, props, init);
    }

    /**
     * Show a modal containing this form.
     *
     * @see {@linkcode renderModal} for the underlying implementation.
     * @returns A promise that resolves when the modal is closed.
     */
    public static showModal(init?: DialogInit): Promise<void> {
        return renderModal(new this(), init);
    }

    /**
     * Show this form in a modal dialog.
     *
     * This is useful when working with a form instance directly, rather than
     * in a Lit HTML template.
     *
     * @see {@linkcode Form.showModal} for the static version.
     * @see {@linkcode renderModal} for the underlying implementation.
     */
    public showModal(init?: DialogInit): Promise<void> {
        return renderModal(this, init);
    }

    //#endregion

    protected logger = ConsoleLogger.prefix(`form/${this.localName}`);

    /**
     * Send the serialized form to its destination.
     *
     * @param data The serialized form data.
     * @returns A promise that resolves when the data has been sent.
     * @abstract
     */
    protected send?(data: NonNullable<D>): Promise<unknown>;

    //#region Properties

    /**
     * Whether the table is visible in the viewport.
     *
     * @remarks
     * We cache the visibility between frames to avoid the synchronous `getBoundingClientRect()`
     * call within {@linkcode isInViewport}.
     */
    @intersectionObserver()
    public visible = false;

    @property({ type: String })
    public successMessage?: string;

    @property({ type: String })
    public autocomplete?: Exclude<AutoFillBase, "">;

    @property({ type: String, useDefault: true })
    public headline?: string | null = null;

    @property({ type: String, useDefault: true })
    public size: PFSize | null = null;

    /**
     * The label for the submit button. If not provided,
     * a default label will be generated based on `verboseName`,
     * falling back to "Create".
     */
    @property({ type: String, attribute: "submit-label", useDefault: true })
    public submitLabel: string | null = null;

    /**
     * The label for the submit button while the form is being submitted. If not provided,
     * a default label will be generated based on `submittingVerb` and `verboseName`,
     * falling back to "Submitting...".
     */
    @property({ type: String, attribute: "submitting-label", useDefault: true })
    public submittingLabel: string | null = null;

    @property({ type: String, attribute: "cancel-label", useDefault: true })
    public cancelButtonLabel: string | null = msg("Cancel");

    @property({ type: Boolean, attribute: "cancelable", useDefault: true })
    public cancelable = true;

    @property({ type: Boolean, attribute: "submittable", useDefault: true })
    public submittable = true;

    //#endregion

    /**
     * A reference to the form element.
     */
    protected formRef = createRef<HTMLFormElement>();

    /**
     * A live reference to the form element, either rendered in-line or slotted.
     */
    public get form(): HTMLFormElement | null {
        if (this.formRef.value) {
            return this.formRef.value;
        }

        const slottedForm =
            this.defaultSlot
                .assignedElements({ flatten: true })
                .find((element): element is HTMLFormElement => {
                    return element instanceof HTMLFormElement;
                }) || null;

        return slottedForm || this.renderRoot.querySelector("form") || null;
    }

    @state()
    protected submitting = false;

    protected sendingOverlay = this.ownerDocument.createElement("ak-loading-overlay");

    @state()
    protected nonFieldErrors: readonly string[] | null = null;

    #verboseName: string | null = null;

    /**
     * Optional singular label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseName` property for this instance.
     */
    @property({ type: String, attribute: "entity-singular" })
    public set verboseName(value: string | null) {
        this.#verboseName = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseName(): string | null {
        return this.#verboseName || (this.constructor as typeof Form).verboseName;
    }

    #verboseNamePlural: string | null = null;

    /**
     * Optional plural label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseNamePlural` property for this instance.
     */
    @property({ type: String, attribute: "entity-plural" })
    public set verboseNamePlural(value: string | null) {
        this.#verboseNamePlural = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseNamePlural(): string | null {
        return this.#verboseNamePlural || (this.constructor as typeof Form).verboseNamePlural;
    }

    protected defaultSlot: HTMLSlotElement = this.ownerDocument.createElement("slot");

    //#endregion

    //#region Formatters

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
        const fallback = pluckFallbackFieldErrors(error);

        return {
            message: msg("There was an error submitting the form."),
            description: pluckErrorDetail(error, fallback[0]),
            level: MessageLevel.error,
        };
    }

    /**
     * An overridable method for formatting the form headline.
     */
    protected formatHeadline(headline = this.headline, modifier?: string | null): string {
        if (headline) {
            return headline;
        }

        const noun = this.verboseName;

        modifier ||= (this.constructor as typeof Form).createLabel;

        if (!noun) {
            return modifier || "";
        }

        return msg(str`${modifier} ${noun}`, {
            id: "model-form.headline",
            desc: "The headline for a form that creates or updates a model instance.",
        });
    }

    /**
     * An overridable method for formatting the submit button label.
     */
    protected formatSubmitLabel(submitLabel = this.submitLabel): string {
        if (submitLabel) {
            return submitLabel;
        }

        const noun = this.verboseName;
        const verb = (this.constructor as typeof Form).submitVerb;

        return noun
            ? msg(str`${verb} ${noun}`, {
                  id: "form.submit.verb-entity",
              })
            : verb;
    }

    /**
     * An overridable method for formatting the message shown while the form is being submitted.
     */
    protected formatSubmittingLabel(submittingLabel = this.submittingLabel): string {
        if (submittingLabel) {
            return submittingLabel;
        }

        const { submittingVerb, verboseName } = this.constructor as typeof Form;

        return msg(str`${submittingVerb} ${verboseName}...`, {
            id: "form.submitting",
            desc: "The message shown while a form is being submitted.",
        });
    }

    //#endregion

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
        const { form } = this;

        if (!form) {
            this.logger.warn("Unable to check validity, no form found", this);
            return true;
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

        const formFields = assignedElements.filter(isFormField);

        if (formFields.length) {
            if (formFields.length === 1) {
                return formFields[0].toJSON() as D;
            }

            throw new TypeError(
                `Multiple form-associated elements found in the form, but no "ak-form-element-horizontal" elements found. Unable to determine which element(s) to serialize.`,
            );
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
     *
     * @returns A promise that resolves to the response from `send()`, or `false` if the form is invalid.
     */
    public submit = <T = unknown>(submitEvent: SubmitEvent): Promise<T | false> => {
        submitEvent.preventDefault();

        if (!this.reportValidity()) {
            return Promise.resolve(false);
        }

        const messageKey = `form-submission-${this.localName}-${Date.now()}`;
        let data: D;

        try {
            data = this.toJSON();
        } catch (error) {
            this.logger.error("An error occurred while serializing the form.", error);

            showMessage({
                level: MessageLevel.error,
                message: msg("An unknown error occurred while submitting the form."),
                description: pluckErrorDetail(error),
                key: messageKey,
            });

            return Promise.resolve(false);
        }

        if (!data) return Promise.resolve(false);

        if (!this.send) {
            this.logger.info("No send() method implemented on form, dispatching submit event");
            this.dispatchEvent(submitEvent);
            return Promise.resolve(false);
        }

        showMessage({
            level: MessageLevel.info,
            icon: "fas fa-spinner fa-spin",
            message: this.formatSubmittingLabel(),
            key: messageKey,
        });

        return this.send(data)
            .then((response) => {
                const successMessage = this.formatAPISuccessMessage(response);

                if (successMessage) {
                    showMessage({
                        ...successMessage,
                        key: messageKey,
                    });
                }

                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );

                // Re-dispatch the submit event so that parent components can listen for it.
                this.dispatchEvent(submitEvent);

                return response as T;
            })
            .catch(async (error: unknown) => {
                if (error instanceof PreventFormSubmit) {
                    if (error.element instanceof HorizontalFormElement) {
                        error.element.errorMessages = [error.message];
                    } else {
                        this.nonFieldErrors = [error.message];
                    }
                } else {
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
                            requestAnimationFrame(() => focusTarget.focus?.());
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

                    const errorMessage = this.formatAPIErrorMessage(parsedError);

                    if (errorMessage) {
                        showMessage({
                            ...errorMessage,
                            key: messageKey,
                        });
                    }
                }

                // Rethrow the error so the form doesn't close.
                throw error;
            });
    };

    protected doSubmit = (event: SubmitEvent): void => {
        if (this.submitting) {
            this.logger.info("Skipping submit. Already submitting!");
        }

        this.submitting = true;

        this.submit(event).finally(() => {
            this.submitting = false;
        });
    };

    protected dispatchSubmit = (): void => {
        return this.doSubmit(
            new SubmitEvent("submit", {
                submitter: this,
                cancelable: true,
                bubbles: true,
                composed: true,
            }),
        );
    };

    //#endregion

    //#region Lifecycle
    public updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("size")) {
            if (this.size) {
                // eslint-disable-next-line wc/no-self-class
                this.classList.add(this.size);
            } else {
                // eslint-disable-next-line wc/no-self-class
                this.classList.remove(...Object.values(PFSize));
            }
        }
    }

    //#endregion

    //#region Render

    protected renderFormWrapper(): SlottedTemplateResult {
        const inline = this.renderForm();

        if (!inline) {
            return this.defaultSlot;
        }

        return html`<form
            id="form"
            ${ref(this.formRef)}
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
        const { headline, assignedSlot, verboseName } = this;

        return guard([force, assignedSlot, verboseName, headline], () => {
            if (
                !force &&
                assignedSlot &&
                (assignedSlot.name === "form" || assignedSlot.name === "")
            ) {
                return null;
            }

            return html`<h1 part="form-header" class="pf-c-title pf-m-2xl">
                ${this.formatHeadline()}
            </h1>`;
        });
    }

    public renderSubmitButton(submitLabel = this.submitLabel): SlottedTemplateResult {
        return html`<button
            type="button"
            class="pf-c-button pf-m-primary"
            @click=${this.dispatchSubmit}
            part="submit-button"
            aria-description=${msg("Submit action")}
        >
            ${this.formatSubmitLabel(submitLabel)}
        </button>`;
    }

    /**
     * An overridable method for rendering the form actions.
     *
     * @remarks
     * If this form is slotted, such as in a modal, this method will not render anything,
     * allowing the slot parent to provide the actions in a more visually appropriate manner.
     */
    public renderActions(force?: boolean): SlottedTemplateResult {
        const { submitLabel, assignedSlot } = this;

        return guard([force, assignedSlot, submitLabel], () => {
            if (
                !force &&
                assignedSlot &&
                (assignedSlot.name === "form" || assignedSlot.name === "")
            ) {
                return null;
            }

            return html`<div part="form-actions" class="pf-c-card__footer">
                ${this.renderSubmitButton()}
            </div>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        if (!this.visible) {
            return nothing;
        }

        return [
            this.submitting ? this.sendingOverlay : nothing,
            this.renderHeader(),
            this.renderNonFieldErrors(),
            this.renderFormWrapper(),
            this.renderActions?.() || null,
        ];
    }

    //#endregion
}
