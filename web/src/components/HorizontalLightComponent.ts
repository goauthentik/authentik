import "#elements/forms/HorizontalFormElement";

import { SlottedTemplateResult } from "../elements/types";

import { AKElement, type AKElementProps } from "#elements/Base";

import { ErrorProp } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { IDGenerator } from "@goauthentik/core/id";

import { html, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

export interface HorizontalLightComponentProps<T> extends AKElementProps {
    name: string;
    label: string | null;
    required?: boolean;
    help: string | null;
    bighelp?: SlottedTemplateResult | SlottedTemplateResult[];
    hidden?: boolean;
    invalid?: boolean;
    errorMessages?: ErrorProp[];
    value?: T;
    inputHint?: string;
}

export abstract class HorizontalLightComponent<T>
    extends AKElement
    implements HorizontalLightComponentProps<T>
{
    // Render into the lightDOM. This effectively erases the shadowDOM nature of this component, but
    // we're not actually using that and, for the meantime, we need the form handlers to be able to
    // find the children of this component.
    //
    // TODO: This abstraction is wrong; it's putting *more* layers in as a way of managing the
    // visual clutter and legibility issues of ak-form-elemental-horizontal and patternfly in
    // general.
    protected createRenderRoot() {
        return this;
    }

    public override role = "presentation";

    //#region Properties

    /**
     * The name attribute for the form element
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    name!: string;

    /**
     * The label for the input control
     * @property
     * @attribute
     */
    @property({ type: String })
    label: string | null = null;

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: false })
    public get required() {
        return this.ariaRequired === "true";
    }

    public set required(value: boolean) {
        this.ariaRequired = value ? "true" : "false";
    }

    /**
     * Help text to display below the form element. Optional
     * @property
     * @attribute
     */
    @property({ reflect: false })
    help: string | null = null;

    /**
     * Extended help content. Optional. Expects to be a TemplateResult
     * @property
     */
    @property({ type: Object })
    bighelp?: TemplateResult | TemplateResult[];

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean })
    public get hidden() {
        return this.ariaHidden === "true";
    }

    public set hidden(value: boolean) {
        this.ariaHidden = value ? "true" : "false";
    }

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    invalid = false;

    /**
     * @property
     */
    @property({ attribute: false })
    public errorMessages?: ErrorProp[];

    /**
     * @property
     */
    @property({ attribute: false })
    value?: T;

    /**
     * Input hint.
     *   - `code`: uses a monospace font and disables spellcheck & autocomplete
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "input-hint" })
    inputHint?: string;

    #fieldID = IDGenerator.elementID().toString();
    protected helpID = `field-help-${this.#fieldID}`;
    protected labelID = `field-label-${this.#fieldID}`;

    /**
     * A unique ID to associate with the input and label.
     * @property
     */
    @property({ type: String, reflect: false })
    public get fieldID() {
        return this.#fieldID;
    }

    public set fieldID(value: string) {
        this.#fieldID = value;
        this.helpID = `field-help-${this.#fieldID}`;
        this.labelID = `field-label-${this.#fieldID}`;
    }

    //#endregion

    //#region Lifecycle

    connectedCallback() {
        super.connectedCallback();
        this.setAttribute("aria-labelledby", this.labelID);
    }

    //#endregion

    //#region Rendering

    /**
     * Render the control element, e.g. an input, textarea, select, etc.
     */
    protected abstract renderControl(): SlottedTemplateResult;

    protected renderHelp(): SlottedTemplateResult | SlottedTemplateResult[] {
        const bigHelp: SlottedTemplateResult[] = Array.isArray(this.bighelp)
            ? this.bighelp
            : [this.bighelp ?? nothing];

        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            ...bigHelp,
        ];
    }

    render() {
        return html`<ak-form-element-horizontal
            .fieldID=${this.fieldID}
            ?required=${this.required}
            ?hidden=${this.hidden}
            name=${this.name}
            role="presentation"
            .errorMessages=${this.errorMessages}
        >
            <div slot="label" class="pf-c-form__group-label">
                ${AKLabel(
                    {
                        id: this.labelID,
                        htmlFor: this.fieldID,
                        required: this.required,
                    },
                    this.label || "",
                )}
            </div>

            ${this.renderControl()}
            <div id=${this.helpID}>${this.renderHelp()}</div>
        </ak-form-element-horizontal> `;
    }

    //#endregion
}
