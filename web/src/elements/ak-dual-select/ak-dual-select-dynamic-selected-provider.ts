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
    @property({ type: Array })
    selected: DualSelectPair[] = [];

    @property({ attribute: false })
    selector: ([key, _]: DualSelectPair) => boolean = ([_key, _]) => false;

    selectedFull: DualSelectPair[] = [];

    willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        if (changed.has("options") || changed.has("selected")) {
            this.selectedFull = Array.from(
                new Set([...this.selected, ...this.options.filter(this.selector)]),
            );
        }
    }

    render() {
        return html`<ak-dual-select
            ${ref(this.dualSelector)}
            .options=${this.options}
            .pages=${this.pagination}
            .selected=${this.selectedFull}
            available-label=${this.availableLabel}
            selected-label=${this.selectedLabel}
        ></ak-dual-select>`;
    }
}
