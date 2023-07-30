import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

type AkFileArgs = {
    // The name of the field, snake-to-camel'd if necessary.
    name: string;
    // The label of the field.
    label: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    value?: any;
    required: boolean;
    // The message to show next to the "current icon".
    current: string;
    // The help message, shown at the bottom.
    help?: string;
};

const akFileDefaults = {
    name: "",
    required: false,
    current: msg("Currently set to:"),
};

export function akFile(args: AkFileArgs) {
    const { name, label, required, value, help, current } = {
        ...akFileDefaults,
        ...args,
    };

    const currentMsg =
        value && current
            ? html` <p class="pf-c-form__helper-text">${current} ${value}</p> `
            : nothing;

    return html`<ak-form-element-horizontal ?required="${required}" label=${label} name=${name}>
        <input type="file" value="" class="pf-c-form-control" />
        ${currentMsg} ${help ? html`<p class="pf-c-form__helper-text">${help}</p>` : nothing}
    </ak-form-element-horizontal>`;
}

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

    @property({ type: String })
    current = msg("Currently set to:");

    @property({ type: String })
    value = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    render() {
        return akFile({
            name: this.name,
            label: this.label,
            value: this.value,
            current: this.current,
            required: this.required,
            help: this.help.trim() !== "" ? this.help : undefined,
        });
    }
}
