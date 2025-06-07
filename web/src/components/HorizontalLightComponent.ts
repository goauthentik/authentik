import { AKElement } from "#elements/Base";
import "#elements/forms/HorizontalFormElement";
import { SlottedTemplateResult } from "#elements/types";
import { IDGenerator } from "@goauthentik/core/id";

import { html, nothing } from "lit";
import { property } from "lit/decorators.js";

export abstract class HorizontalLightComponent<T> extends AKElement {
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

    @property({ type: String, reflect: true })
    name!: string;

    @property({ type: String, reflect: true })
    label = "";

    @property({ type: Boolean, reflect: true })
    required = false;

    @property({ type: String, reflect: true })
    help = "";

    @property({ type: Object })
    bighelp?: SlottedTemplateResult | SlottedTemplateResult[];

    @property({ type: Boolean, reflect: true })
    hidden = false;

    @property({ type: Boolean, reflect: true })
    invalid = false;

    @property({ attribute: false })
    errorMessages: string[] = [];

    @property({ attribute: false })
    value?: T;

    @property({ type: String, attribute: "input-hint" })
    inputHint = "";

    protected fieldID = IDGenerator.elementID().toString();

    abstract renderControl(): SlottedTemplateResult;

    renderHelp(): SlottedTemplateResult[] {
        const bigHelp = Array.isArray(this.bighelp) ? this.bighelp : [this.bighelp ?? nothing];

        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            ...bigHelp,
        ];
    }

    render() {
        return html`<ak-form-element-horizontal
            fieldID=${this.fieldID}
            label=${this.label}
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
