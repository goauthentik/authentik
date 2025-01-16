import { bound } from "@goauthentik/elements/decorators/bound";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { availablePaneStyles } from "./styles.css";

import {
    DualSelectMoveAvailableEvent,
    DualSelectMoveRequestEvent,
    DualSelectUpdateEvent,
} from "../events";
import type { DualSelectPair } from "../types";
import { AkDualSelectAbstractPane } from "./ak-dual-select-pane";

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
export class AkDualSelectAvailablePane extends AkDualSelectAbstractPane {
    static get styles() {
        return [...AkDualSelectAbstractPane.styles, availablePaneStyles];
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

    @bound
    onClick(key: string) {
        if (this.selected.has(key)) {
            return;
        }
        this.move(key);
        this.dispatchEvent(new DualSelectMoveAvailableEvent(this.moveable.sort()));
        this.dispatchEvent(new DualSelectUpdateEvent());
        // Necessary because updating a map won't trigger a state change
        this.requestUpdate();
    }

    @bound
    onMove(key: string) {
        this.toMove.delete(key);
        this.dispatchEvent(new DualSelectMoveRequestEvent("add-one", key));
        this.requestUpdate();
    }

    // DO NOT use `Array.map()` instead of Lit's `map()` function. Lit's `map()` is object-aware and
    // will not re-arrange or reconstruct the list automatically if the actual sources do not
    // change; this allows the available pane to illustrate selected items with the checkmark
    // without causing the list to scroll back up to the top.

    override render() {
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
