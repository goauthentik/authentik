import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { decodeCrontab } from "#elements/Crontab_impl/decodeCrontab";
import { WithLocale } from "#elements/mixins/locale";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-cron-input")
export class AKCronInput extends WithLocale(HorizontalLightComponent<string>) {
    /**
     * @property
     * @attribute
     */
    @property({ type: String })
    public value = "";

    /**
     * @property
     * @attribute
     */
    @property({ type: Boolean, attribute: "readonly" })
    public readOnly = false;

    #inputListener(ev: InputEvent) {
        this.value = (ev.target as HTMLInputElement).value;
    }

    protected override renderControl(): SlottedTemplateResult {
        return html`<input
            type="text"
            name=${this.name}
            @input=${this.#inputListener}
            id=${ifDefined(this.fieldID)}
            value=${ifDefined(this.value)}
            class="pf-c-form-control pf-m-monospace"
            aria-describedby=${this.helpID}
            autocomplete="off"
            spellcheck="false"
            ?required=${this.required}
            ?readonly=${this.readOnly}
            ?autofocus=${this.autofocus}
            ${this.autofocusTarget.toRef()}
        />`;
    }

    public get decode() {
        return decodeCrontab(this.value, this.activeLanguageTag);
    }

    protected override renderHelp(): SlottedTemplateResult {
        if (!this.value?.trim()) return nothing;

        return html`<p class="pf-c-form__helper-text">${this.decode}</p>`;
    }
}

export default AkCronInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-cron-input": AkCronInput;
    }
}
