import "#elements/EmptyState";

import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { asInstanceInvoker } from "#elements/dialogs";
import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { ConsoleLogger } from "#logger/browser";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";
import { property, state } from "lit/decorators.js";

interface NamedInstance {
    verboseName?: string;
    verboseNamePlural?: string;
}

/**
 * Predicate to determine if a given instance has verbose name properties.
 *
 * This is useful for plucking out the labels for dynamic forms.
 */
function isNamedInstance(instance: unknown): instance is NamedInstance {
    if (!instance || typeof instance !== "object") {
        return false;
    }

    return "verboseName" in instance || "verboseNamePlural" in instance;
}

/**
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in. Handles loading and tracking of the instance.
 *
 * @template T The type of the model instance.
 * @template PKT The type of the primary key of the model instance.
 * @template D The result of `toJSON()`, which is the data sent to the server on submit.
 *
 * @prop {T} instance - The current instance being edited or viewed.
 * @prop {PKT} instancePk - The primary key of the instance to load.
 */
export abstract class ModelForm<
    T extends object | null = object,
    PKT extends string | number = string | number,
    D = T,
> extends Form<T, D> {
    /**
     * The modifier to use in the default headline when editing an instance, e.g. "Edit".
     */
    public static modifierLabel: string | null = msg("Edit", {
        id: "form.modifier.edit",
    });

    /**
     * The label to use for the submit button when editing an instance, e.g. "Save Changes".
     */
    public static saveLabel: string | null = msg("Save Changes", {
        id: "form.submit.save-changes",
    });

    /**
     * The label to use for the submit button while the form is being submitted
     * when editing an instance, e.g. "Saving Changes...".
     */
    public static savingLabel: string | null = msg("Saving Changes...", {
        id: "form.submit.saving-changes",
    });

    /**
     * A helper method to create an invoker for editing an instance of this form.
     *
     * The invoker will look for a `data-pk` attribute on the clicked element to determine which instance to load.
     *
     * @see {@linkcode Form.asModalInvoker} for opening a blank form in a modal.
     * @see {@linkcode asInvoker} for the underlying implementation.
     */
    public static asInstanceInvoker = asInstanceInvoker;

    protected logger = ConsoleLogger.prefix(`model-form/${this.localName}`);

    @state()
    protected error: APIError | null = null;

    @state()
    protected loading = false;

    protected abortController: AbortController | null = null;

    /**
     * An overridable method for loading an instance.
     *
     * @param pk The primary key of the instance to load.
     * @returns A promise that resolves to the loaded instance.
     */
    protected abstract loadInstance(pk: PKT): Promise<T | null>;

    /**
     * An overridable method for assigning the loaded instance to the form's state.
     *
     * This can be used to intercept the loaded instance before it's set on the form.
     */
    protected assignInstance(instance: T | null): void {
        this.instance = instance;

        if (instance && isNamedInstance(instance)) {
            this.verboseName = instance.verboseName ?? this.verboseName;
            this.verboseNamePlural = instance.verboseNamePlural ?? this.verboseNamePlural;
        }
    }

    /**
     * An overridable method for loading any data, beyond the instance.
     *
     *
     * @see {@linkcode loadInstance}
     * @returns A promise that resolves when the data has been loaded.
     */
    protected async load?(): Promise<void | boolean>;

    /**
     * Timestamp of last call to {@linkcode load}.
     * Used to prevent multiple calls to `load` when the form is rapidly shown and hidden.
     */
    #loadedAt: Date | null = null;

    @property({
        attribute: "pk",
        useDefault: true,
        converter: { fromAttribute: (value) => value as PKT },
    })
    public instancePk: PKT | null = null;

    @property({ attribute: false, useDefault: true })
    public instance: T | null = this.createDefaultInstance();

    //#region Public methods

    /**
     * Resets the form to its initial state, including clearing the loaded instance and any errors.
     */
    public override reset(): void {
        super.reset();

        this.instance = null;
        this.error = null;
    }

    /**
     * A helper method to create a default instance when the form is used for creation instead of editing.
     *
     * By default, this returns `null`, but it can be overridden to provide a default instance with pre-filled values.
     *
     * @returns A default instance of the model, or null if not applicable.
     */
    public createDefaultInstance(): T | null {
        return null;
    }

    //#endregion

    protected override formatSubmitLabel(submitLabel?: string): string {
        const { saveLabel } = this.constructor as typeof ModelForm;

        if (this.instancePk && saveLabel) {
            return saveLabel;
        }

        return super.formatSubmitLabel(submitLabel);
    }

    protected override formatSubmittingLabel(submittingLabel?: string): string {
        const { savingLabel } = this.constructor as typeof ModelForm;

        if (this.instancePk && savingLabel) {
            return savingLabel;
        }

        return super.formatSubmittingLabel(submittingLabel);
    }

    protected override formatHeadline(modifier?: string | null): string {
        modifier ||= this.instancePk ? (this.constructor as typeof ModelForm).modifierLabel : null;

        return super.formatHeadline(this.headline, modifier);
    }

    //#region Lifecycle

    /**
     * Loads the instance when the form is shown, handing loading and error states.
     */
    protected doLoad() {
        if (this.#loadedAt || this.loading) {
            return Promise.resolve();
        }

        if (this.load) {
            this.loading = true;
        }

        const loadPromise = this.load?.() || Promise.resolve(true);

        return loadPromise
            .then((result) => {
                this.#loadedAt = new Date();

                if (result === false) {
                    this.logger.debug("Load method returned false, skipping instance load");
                    return;
                }

                return this.refresh();
            })
            .catch(this.delegateError)
            .finally(() => {
                this.loading = false;
            });
    }

    /**
     * A helper method to retry loading the instance after an error has occurred.
     */
    protected retryLoad = (): Promise<void> => {
        this.error = null;
        this.#loadedAt = null;
        return this.doLoad();
    };

    /**
     * Refreshes the instance by re-calling `loadInstance` with the current `instancePk`.
     */
    @listen(AKRefreshEvent)
    public refresh = async (): Promise<void> => {
        if (!this.instancePk) {
            this.logger.info("Skipping refresh. No instance PK provided.");
            return;
        }

        this.error = null;
        this.loading = true;

        return this.loadInstance(this.instancePk)
            .then((instance) => this.assignInstance(instance))
            .catch(this.delegateError)
            .finally(() => {
                this.loading = false;
            });
    };

    /**
     * Prepares a loading error for display in the form's template.
     *
     * @param error The error to prepare.
     */
    protected delegateError = async (error: unknown): Promise<void> => {
        this.error = await parseAPIResponseError(error);
    };

    protected override render(): SlottedTemplateResult {
        if (!this.visible) {
            return null;
        }

        if (!this.#loadedAt) {
            // If there is anything to do load, we do so asynchronously,
            // possibly updating our loading flag to avoid an unnecessary
            // visual change if the load is very fast.
            this.doLoad();
        }

        if (this.loading) {
            // We avoid the delayed fade-in of the loading state to prevent flickering.
            const ready = this.instance || this.#loadedAt;

            this.logger.debug("Form is loading, showing loading state", {
                ready,
                instance: !!this.instance,
                loadedAt: !!this.#loadedAt,
            });
            return html`<ak-empty-state
                class="${ready ? "" : "ak-fade-in ak-m-delayed"}"
                loading
            ></ak-empty-state>`;
        }

        if (this.error && !this.#loadedAt) {
            // The form is in an error state and has not successfully loaded before.
            return html`<ak-empty-state icon="pf-icon-warning-triangle" part="error-state">
                <span>${msg(str`An error occurred while loading ${this.verboseName}.`)}</span>
                <div slot="body">
                    <p>${pluckErrorDetail(this.error)}</p>

                    <button class="pf-c-button pf-m-primary" @click=${this.retryLoad}>
                        ${msg("Retry")}
                    </button>
                </div>
            </ak-empty-state>`;
        }

        // Otherwise, render the form as normal.
        // If there was an error but we have successfully loaded before,
        // we allow the form to render with the previous data and show the
        // error message through the normal channels (e.g. non-field errors).
        return super.render();
    }

    //#endregion
}
