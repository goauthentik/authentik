import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { availablePaneStyles, listStyles } from "./styles.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EVENT_ADD_ONE } from "../constants";
import type { DualSelectPair } from "../types";

const styles = [PFBase, PFButton, PFDualListSelector, listStyles, availablePaneStyles];

const hostAttributes = [
    ["aria-labelledby", "dual-list-selector-available-pane-status"],
    ["aria-multiselectable", "true"],
    ["role", "listbox"],
];

/**
 * @element ak-dual-select-available-panel
 *
 * The "available options" or "left" pane in a dual-list multi-select. It receives from its parent a
 * list of options to show *now*, the list of all "selected" options, and maintains an internal list
 * of objects selected to move. "selected" options are marked with a checkmark to show they're
 * already in the "selected" collection and would be pointless to move.
 *
 * @fires ak-dual-select-available-move-changed - When the list of "to move" entries changed.
 * Includes the current * `toMove` content.
 *
 * @fires ak-dual-select-add-one - Double-click with the element clicked on.
 *
 * It is not expected that the `ak-dual-select-available-move-changed` event will be used; instead,
 * the attribute will be read by the parent when a control is clicked.
 *
 */
@customElement("ak-dual-select-available-pane")
export class AkDualSelectAvailablePane extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    /* The array of key/value pairs this pane is currently showing */
    @property({ type: Array })
    readonly options: DualSelectPair[] = [];

    /* A set (set being easy for lookups) of keys with all the pairs selected, so that the ones
     * currently being shown that have already been selected can be marked and their clicks ignored.
     *
     */
    @property({ type: Object })
    readonly selected: Set<string> = new Set();

    /* This is the only mutator for this object. It collects the list of objects the user has
     * clicked on *in this pane*. It is explicitly marked as "public" to emphasize that the parent
     * orchestrator for the dual-select widget can and will access it to get the list of keys to be
     * moved (removed) if the user so requests.
     *
     */
    @state()
    public toMove: Set<string> = new Set();

    constructor() {
        super();
        this.onClick = this.onClick.bind(this);
        this.onMove = this.onMove.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        hostAttributes.forEach(([attr, value]) => {
            if (!this.hasAttribute(attr)) {
                this.setAttribute(attr, value);
            }
        });
    }

    clearMove() {
        this.toMove = new Set();
    }

    onClick(key: string) {
        if (this.selected.has(key)) {
            return;
        }
        if (this.toMove.has(key)) {
            this.toMove.delete(key);
        } else {
            this.toMove.add(key);
        }
        this.dispatchCustomEvent(
            "ak-dual-select-available-move-changed",
            Array.from(this.toMove.values()).sort(),
        );
        this.dispatchCustomEvent("ak-dual-select-move");
        // Necessary because updating a map won't trigger a state change
        this.requestUpdate();
    }

    onMove(key: string) {
        this.toMove.delete(key);
        this.dispatchCustomEvent(EVENT_ADD_ONE, key);
        this.requestUpdate();
    }

    get moveable() {
        return Array.from(this.toMove.values());
    }

    // DO NOT use `Array.map()` instead of Lit's `map()` function. Lit's `map()` is object-aware and
    // will not re-arrange or reconstruct the list automatically if the actual sources do not
    // change; this allows the available pane to illustrate selected items with the checkmark
    // without causing the list to scroll back up to the top.

    render() {
        return html`
            <div class="pf-c-dual-list-selector__menu">
                <ul class="pf-c-dual-list-selector__list">
                    ${map(this.options, ([key, label]) => {
                        const selected = classMap({
                            "pf-m-selected": this.toMove.has(key),
                        });
                        return html` <li
                            class="pf-c-dual-list-selector__list-item"
                            aria-selected="false"
                            @click=${() => this.onClick(key)}
                            @dblclick=${() => this.onMove(key)}
                            role="option"
                            data-ak-key=${key}
                            tabindex="-1"
                        >
                            <div class="pf-c-dual-list-selector__list-item-row ${selected}">
                                <span class="pf-c-dual-list-selector__item">
                                    <span class="pf-c-dual-list-selector__item-main">
                                        <span class="pf-c-dual-list-selector__item-text"
                                            ><span>${label}</span>${this.selected.has(key)
                                                ? html`<span
                                                      class="pf-c-dual-list-selector__item-text-selected-indicator"
                                                      ><i class="fa fa-check"></i
                                                  ></span>`
                                                : nothing}</span
                                        ></span
                                    ></span
                                >
                            </div>
                        </li>`;
                    })}
                </ul>
            </div>
        `;
    }
}

export default AkDualSelectAvailablePane;

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-available-pane": AkDualSelectAvailablePane;
    }
}
