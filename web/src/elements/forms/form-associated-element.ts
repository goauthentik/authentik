import { AKElement } from "#elements/Base";

import { Jsonifiable } from "type-fest";

import { msg } from "@lit/localize";
import { LitElement } from "lit";
import { property } from "lit/decorators.js";
import { createRef, Ref } from "lit/directives/ref.js";

/**
 * A subset of form associated {@linkcode ElementInternals} properties.
 *
 * @see {@linkcode FormAssociatedElement} for usage.
 */
export interface FormAssociated extends Pick<
    ElementInternals,
    | "form"
    | "validity"
    | "validationMessage"
    | "willValidate"
    | "labels"
    | "checkValidity"
    | "reportValidity"
> {
    /**
     * The name of the input, provided to the form.
     */
    name: string | null;

    /**
     * The type of the input, provided to the form.
     */
    type: string;

    /**
     * Whether or not the input is required.
     */
    required?: boolean;

    /**
     * Whether or not the input is read-only.
     */
    readonly?: boolean;

    /**
     * A JSON representation of the value.
     */
    toJSON(): Jsonifiable;
}

export type FormValue = File | string | FormData | null;

/**
 * A base element which provides reactive properties and methods for interacting with a parent form.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/ElementInternals | MDN}
 */
export abstract class FormAssociatedElement<
    V extends FormValue = string,
    T extends Jsonifiable = V extends string ? V : Jsonifiable,
    S extends FormValue = V,
>
    extends AKElement
    implements FormAssociated
{
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    public static readonly formAssociated = true;

    /**
     * The internals of the element.
     *
     * @protected
     * @see {@linkcode FormAssociated}
     */
    protected internals = this.attachInternals();

    //#region Reactive Properties

    @property({ type: Boolean })
    public get required() {
        return this.internals.ariaRequired === "true";
    }

    public set required(value: boolean) {
        this.internals.ariaRequired = value ? "true" : "false";
    }

    @property({ type: Boolean, attribute: "readonly" })
    public get readOnly() {
        return this.internals.ariaReadOnly === "true";
    }

    public set readOnly(value: boolean) {
        this.internals.ariaReadOnly = value ? "true" : "false";
    }

    @property({ type: Boolean })
    public get disabled() {
        return this.internals.ariaDisabled === "true";
    }

    public set disabled(value: boolean) {
        this.internals.ariaDisabled = value ? "true" : "false";
    }

    //#endregion

    //#region Aliased Properties

    public get form(): HTMLFormElement | null {
        return this.internals.form;
    }

    @property({ type: String, reflect: true })
    name: string | null = null;

    public get type() {
        return this.localName;
    }

    public get validity() {
        return this.internals.validity;
    }

    public get validationMessage() {
        return this.internals.validationMessage;
    }

    public get willValidate() {
        return this.internals.willValidate;
    }

    public get labels() {
        return this.internals.labels;
    }

    //#endregion

    //#region Values

    /**
     * A reference to an element that is focusable when validation fails.
     */
    protected anchorRef: Ref<HTMLElement>;

    /**
     * The element that is focusable when validation fails.
     */
    declare protected anchor: HTMLElement | null;

    /**
     * Set the value of the form.
     *
     * @param value The value visible to the form during submission.
     * @param state The value as provided by the user.
     */
    protected setFormValue(value: V, state?: S) {
        this.internals.setFormValue(value, state);

        if (this.required) {
            if (value) {
                this.internals.setValidity({});
            } else {
                this.internals.setValidity(
                    {
                        valueMissing: true,
                    },
                    msg("This field is required."),
                    this.anchorRef.value,
                );
            }
        }
    }

    public abstract toJSON(): T;

    //#endregion

    //#region Validation

    public checkValidity = this.internals.checkValidity.bind(this.internals);
    public reportValidity = this.internals.reportValidity.bind(this.internals);

    //#endregion

    /**
     * Set the validity state of the form.
     *
     * @param flags The validity state flags.
     * @param message The validation message.
     * @param element The element to set the validity state on.
     */
    protected setValidity(flags: ValidityStateFlags = {}, message?: string, element?: HTMLElement) {
        this.internals.setValidity(flags, message, element ?? this.anchorRef.value);
    }

    //#endregion

    public constructor() {
        super();
        this.anchorRef = createRef<HTMLElement>();

        // We define the getter here to allow the base type to be extended,
        // letting the subclasses define a more accurate HTMLElement type.
        Object.defineProperty(this, "anchor", {
            get() {
                return this.anchorRef.value || null;
            },
            enumerable: true,
            configurable: true,
        });
    }
}
