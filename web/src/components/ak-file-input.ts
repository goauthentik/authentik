import { HorizontalLightComponent } from "#components/HorizontalLightComponent";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-file-input")
export class AkFileInput extends HorizontalLightComponent<string> {
    #inputRef = createRef<HTMLInputElement>();

    get files(): Iterable<File> {
        return this.#inputRef.value?.files || [];
    }

    #inputListener(ev: InputEvent) {
        this.value = (ev.target as HTMLInputElement).value;
    }

    public override renderControl() {
        return html` <input
            ${ref(this.#inputRef)}
            id=${ifDefined(this.fieldID)}
            type="file"
            @input=${this.#inputListener}
            value=${ifDefined(this.value)}
            class="pf-c-form-control"
            ?required=${ifDefined(this.required)}
        />`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-input": AkFileInput;
    }
}
