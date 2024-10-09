import { AKElement } from "@goauthentik/elements/Base";

import { html } from "lit";
import { property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const _textTypes = ["text", "url", "tel", "email", "password"] as const;
export type TextTypes = (typeof _textTypes)[number];

export class FormAwareControl extends AKElement {
    static formAssociated = true;

    static akControlElement = true;

    _internals: ElementInternals;

    constructor() {
        super();
        this._internals = this.attachInternals();
    }

    // The following properties and methods aren't strictly required,
    // but browser-level form controls provide them. Providing them helps
    // ensure consistency with browser-provided controls.
    get form() {
        return this.internals_.form;
    }
    get validity() {
        return this.internals_.validity;
    }
    get validationMessage() {
        return this.internals_.validationMessage;
    }
    get willValidate() {
        return this.internals_.willValidate;
    }
    checkValidity() {
        return this.internals_.checkValidity();
    }
    reportValidity() {
        return this.internals_.reportValidity();
    }
}

export class InputField extends FormAwareControl {
    public static override get styles() {
        return [PFBase, PFFormControl];
    }

    @property({ type: String })
    public type = "text";

    @property({ type: Number })
    public minlength = -1;

    @property({ type: Number })
    public maxlength = -1;

    @property({ type: Boolean })
    public disabled = false;

    @property({ type: Boolean })
    public required = false;

    @property({ type: Boolean })
    public readonly = false;

    @property({ type: String })
    public value = "";

    @property({ type: String })
    public placeholder?: string;

    @property({ type: String })
    set pattern(p: string) {
        try {
            this._pattern = new RegExp(p);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (_e: any) {
            this._pattern = undefined;
            console.warn(
                `Pattern provided to ${this.tagName.toLowerCase()} is not a valid regular expression`,
            );
        }
    }

    get pattern() {
        return this._pattern;
    }

    private _pattern?: RegExp;

    @query("input")
    protected inputElement!: HTMLInputElement;

    get json() {
        return this.value;
    }

    checkValidity(value: string) {
        if (value === "" && this.required) {
            this.internals.setValidity(
                { valueMissing: true },
                msg("This field is required"),
                this.inputElement,
            );
            return false;
        }

        if (this.minLength > -1 && value.length < this.minLength) {
            this.internals.setValidity(
                { tooShort: true },
                msg("This value is too short"),
                this.inputElement,
            );
            return false;
        }

        if (this.maxLength > -1 && value.length > this.maxnLength) {
            this.internals.setValidity(
                { tooLong: true },
                msg("This value is too long"),
                this.inputElement,
            );
            return false;
        }

        if (this.pattern && !this.pattern.test(value)) {
            this.internals_.setValidity(
                { patternMismatch: true },
                msg("The value does not match the pattern provided"),
                this.inputElement,
            );
            return false;
        }
        this.setValidity({ valid: true }, "", this.inputElement);
        return true;
    }

    protected onInput(_event: Event) {
        this._internals.setFormValue(this.inputElement.value);
        this.check_validity(this.inputElement.value);
        this.dispatchEvent(new Event("input", eventFlags));
    }

    protected onChange(_event) {
        this._interals.setFormValue(this.inputElement.value);
        this.dispatchEvent(new Event("change", eventFlags));
    }

    firstUpdated(...args) {
        super.firstUpdated(...args);
        this._internals.setFormValue(this.value);
    }

    render() {
        const classes = classMap({
            "pf-c-form-control": true,
        });

        return html`
        <input
        ${classes}
        name=${ifDefined(this.name)}
        type=${this.type}
        aria-invalid=${ifDefined(this.invalid)}
        maxlength=${ifDefined(this.maxlength > -1 ? this.maxlength : undefined)}
        minlength=${ifDefined(this.minlength > -1 ? this.minlength : undefined)}
        pattern=${ifDefined(this.pattern)}
        placeholder=${this.placeholder}
        value=${live(this.value)}
        ?disabled=${this.disabled}
        ?required=${this.required}
        ?readonly=${this.readonly}
        @change=${this.onChange}
        @input=${this.onInput}
        ></input>`;
    }
}
