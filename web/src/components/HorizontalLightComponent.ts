import { AKElement, type AKElementProps } from "#elements/Base";
import "#elements/forms/HorizontalFormElement";
import { SlottedTemplateResult } from "#elements/types";
import { IDGenerator } from "@goauthentik/core/id";

import { html, nothing } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export interface HorizontalLightComponentProps<T> extends AKElementProps {
    name: string;
    label?: string;
    required?: boolean;
    help?: string;
    bighelp?: SlottedTemplateResult | SlottedTemplateResult[];
    hidden?: boolean;
    invalid?: boolean;
    errorMessages?: string[];
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

    /**
     * The name attribute for the form element
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    public name!: string;

    /**
     * The label for the input control
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    public label?: string;

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    public required = false;

    /**
     * Help text to display below the form element. Optional
     * @property
     * @attribute
     */
    @property({ type: String, reflect: true })
    public help = "";

    /**
     * Extended help content. Optional. Expects to be a TemplateResult
     * @property
     */
    @property({ type: Object })
    public bighelp?: SlottedTemplateResult | SlottedTemplateResult[];

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    public hidden = false;

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, reflect: true })
    public invalid = false;

    /**
     * @property
     */
    @property({ attribute: false })
    public errorMessages: string[] = [];

    /**
     * @attribute
     * @property
     */
    @property({ attribute: false })
    public value?: T;

    /**
     * Input hint.
     *   - `code`: uses a monospace font and disables spellcheck & autocomplete
     * @property
     * @attribute
     */
    @property({ type: String, attribute: "input-hint" })
    public inputHint?: string;

    protected renderControl() {
        throw new Error("Must be implemented in a subclass");
    }

    protected fieldID = IDGenerator.elementID().toString();

    protected renderHelp(): SlottedTemplateResult | SlottedTemplateResult[] {
        const bigHelp = Array.isArray(this.bighelp) ? this.bighelp : [this.bighelp ?? nothing];

        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            ...bigHelp,
        ];
    }

    render() {
        return html`<ak-form-element-horizontal
            fieldID=${this.fieldID}
            label=${ifDefined(this.label)}
            ?required=${this.required}
            ?hidden=${this.hidden}
            name=${this.name}
            .errorMessages=${this.errorMessages}
            ?invalid=${this.invalid}
        >
            ${this.renderControl()} ${this.renderHelp()}
        </ak-form-element-horizontal> `;
    }
}
