import { PropertyValues, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ref } from "lit/directives/ref.js";

import { AkDualSelectProvider } from "./ak-dual-select-provider.js";
import "./ak-dual-select.js";
import type { DualSelectPair } from "./types.js";

/**
 * @element ak-dual-select-dynamic-provider
 *
 * A top-level component for multi-select elements have dynamically generated "selected"
 * lists.
 */

@customElement("ak-dual-select-dynamic-selected")
export class AkDualSelectDynamic extends AkDualSelectProvider {
    /**
     * An extra source of "default" entries. A number of our collections have an alternative default
     * source when initializing a new component instance of that collection's host object. Only run
     * on start-up.
     *
     * @attr
     */
    @property({ attribute: false })
    selector: ([key, _]: DualSelectPair) => boolean = ([_key, _]) => false;

    private firstUpdateHasRun = false;

    willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        // On the first update *only*, even before rendering, when the options are handed up, update
        // the selected list with the contents derived from the selector.
        if (!this.firstUpdateHasRun && this.options.length > 0) {
            this.firstUpdateHasRun = true;
            this.selected = Array.from(
                new Set([...this.selected, ...this.options.filter(this.selector)]),
            );
        }
    }

    render() {
        return html`<ak-dual-select
            ${ref(this.dualSelector)}
            .options=${this.options}
            .pages=${this.pagination}
            .selected=${this.selected}
            available-label=${this.availableLabel}
            selected-label=${this.selectedLabel}
        ></ak-dual-select>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-dynamic-selected": AkDualSelectDynamic;
    }
}
