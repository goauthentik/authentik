import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, query } from "lit/decorators.js";

@customElement("ak-file-input")
export class AkFileInput extends AKElement {
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

    /*
     * The message to show next to the "current icon".
     *
     * @attr
     */
    @property({ type: String })
    current = msg("Currently set to:");

    @property({ type: String })
    value = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    @query('input[type="file"]')
    input!: HTMLInputElement;

    get files() {
        return this.input.files;
    }

    render() {
        const currentMsg =
            this.value && this.current
                ? html` <p class="pf-c-form__helper-text">${this.current} ${this.value}</p> `
                : nothing;

        return html`<ak-form-element-horizontal
            ?required="${this.required}"
            label=${this.label}
            name=${this.name}
        >
            <input type="file" value="" class="pf-c-form-control" />
            ${currentMsg}
            ${this.help.trim() ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
        </ak-form-element-horizontal>`;
    }
}
