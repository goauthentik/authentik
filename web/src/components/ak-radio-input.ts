import { RadioOption } from "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/Radio";
import { HorizontalLightComponent } from "./HorizontalLightComponent";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-radio-input")
export class AkRadioInput<T> extends HorizontalLightComponent {
    @property({ type: Object })
    value!: T;

    @property({ type: Array })
    options: RadioOption<T>[] = [];

    handleInput(ev: CustomEvent) {
        if ("detail" in ev) {
            this.value = ev.detail.value;
        }
    }

    renderHelp() {
        // This is weird, but Typescript says it's necessary?
        return [nothing as typeof nothing];
    }

    renderControl() {
        return html`<ak-radio
                .options=${this.options}
                .value=${this.value}
                @input=${this.handleInput}
            ></ak-radio>
            ${this.help.trim()
                ? html`<p class="pf-c-form__helper-radio">${this.help}</p>`
                : nothing}`;
    }
}

export default AkRadioInput;
