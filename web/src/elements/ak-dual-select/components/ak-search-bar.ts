import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { SearchbarEventDetail, SearchbarEventSource } from "../types.ts";
import { globalVariables, searchStyles } from "./search.css.js";

@customElement("ak-search-bar")
export class AkSearchbar extends CustomEmitterElement(AKElement) {
    static styles = [PFBase, globalVariables, searchStyles];

    @property({ type: String, reflect: true })
    public value = "";

    /**
     * If you're using more than one search, this token can help listeners distinguishing between
     * those searches. Lit's own helpers sometimes erase the source and current targets.
     */
    @property({ type: String })
    public name?: SearchbarEventSource;

    protected inputRef = createRef<HTMLInputElement>();

    #changeListener = () => {
        const inputElement = this.inputRef.value;

        if (inputElement) {
            this.value = inputElement.value;
        }

        if (!this.name) {
            console.warn("ak-search-bar: no name provided, event will not be dispatched");
            return;
        }

        this.dispatchCustomEvent<SearchbarEventDetail>("ak-search", {
            source: this.name,
            value: this.value,
        });
    };

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
                            ${ref(this.inputRef)}
                            @input=${this.#changeListener}
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
