import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/HorizontalFormElement.js";

import { TemplateResult, html, nothing } from "lit";
import { property } from "lit/decorators.js";

type HelpType = TemplateResult | typeof nothing;

export class HorizontalLightComponent<T> extends AKElement {
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

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    @property({ type: Object })
    bighelp?: TemplateResult | TemplateResult[];

    @property({ type: Boolean })
    hidden = false;

    @property({ type: Boolean })
    invalid = false;

    @property({ attribute: false })
    errorMessages: string[] = [];

    @property({ attribute: false })
    value?: T;

    @property({ type: String })
    inputHint = "";

    renderControl() {
        throw new Error("Must be implemented in a subclass");
    }

    renderHelp(): HelpType[] {
        const bigHelp: HelpType[] = Array.isArray(this.bighelp)
            ? this.bighelp
            : [this.bighelp ?? nothing];
        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            ...bigHelp,
        ];
    }

    render() {
        // prettier-ignore
        return html`<ak-form-element-horizontal
            label=${this.label}
            ?required=${this.required}
            ?hidden=${this.hidden}
            name=${this.name}
            .errorMessages=${this.errorMessages}
            ?invalid=${this.invalid}
            >
              ${this.renderControl()}
              ${this.renderHelp()}
        </ak-form-element-horizontal> `;
    }
}
