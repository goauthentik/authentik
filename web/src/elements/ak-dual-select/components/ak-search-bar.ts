import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import type { Ref } from "lit/directives/ref.js";

import { globalVariables, searchStyles } from "./search.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { SearchbarEventDetail } from "../types";

const styles = [PFBase, globalVariables, searchStyles];

@customElement("ak-search-bar")
export class AkSearchbar extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    @property({ type: String, reflect: true })
    value = "";

    /**
     * If you're using more than one search, this token can help listeners distinguishing between
     * those searches. Lit's own helpers sometimes erase the source and current targets.
     */
    @property({ type: String })
    name = "";

    input: Ref<HTMLInputElement> = createRef();

    constructor() {
        super();
        this.onChange = this.onChange.bind(this);
    }

    onChange(_event: Event) {
        if (this.input.value) {
            this.value = this.input.value.value;
        }
        this.dispatchCustomEvent<SearchbarEventDetail>("ak-search", {
            source: this.name,
            value: this.value,
        });
    }

    render() {
        return html`
            <div class="pf-c-text-input-group">
                <div class="pf-c-text-input-group__main pf-m-icon">
                    <span class="pf-c-text-input-group__text"
                        ><span class="pf-c-text-input-group__icon"
                            ><i class="fa fa-search fa-fw"></i></span
                        ><input
                            type="search"
                            class="pf-c-text-input-group__text-input"
                            ${ref(this.input)}
                            @input=${this.onChange}
                            value="${this.value}"
                    /></span>
                </div>
            </div>
        `;
    }
}

export default AkSearchbar;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-bar": AkSearchbar;
    }
}
