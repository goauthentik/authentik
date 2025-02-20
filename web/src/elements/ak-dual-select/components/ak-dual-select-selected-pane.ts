import { bound } from "@goauthentik/elements/decorators/bound";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { selectedPaneStyles } from "./styles.css";

import {
    DualSelectMoveRequestEvent,
    DualSelectMoveSelectedEvent,
    DualSelectUpdateEvent,
} from "../events";
import type { DualSelectPair } from "../types";
import { AkDualSelectAbstractPane } from "./ak-dual-select-pane";

/**
 * @element ak-dual-select-available-panel
 *
 * The "selected options" or "right" pane in a dual-list multi-select.  It receives from its parent
 * a list of the selected options, and maintains an internal list of objects selected to move.
 *
 * @fires ak-dual-select-selected-move-changed - When the list of "to move" entries changed.
 * Includes the current `toMove` content.
 *
 * @fires ak-dual-select-remove-one - Double-click with the element clicked on.
 *
 * It is not expected that the `ak-dual-select-selected-move-changed` will be used; instead, the
 * attribute will be read by the parent when a control is clicked.
 *
 */
@customElement("ak-dual-select-selected-pane")
export class AkDualSelectSelectedPane extends AkDualSelectAbstractPane {
    static get styles() {
        return [...AkDualSelectAbstractPane.styles, selectedPaneStyles];
    }

    /* The array of key/value pairs that are in the selected list.  ALL of them. */
    @property({ type: Array })
    readonly selected: DualSelectPair[] = [];

    @bound
    onClick(key: string) {
        this.move(key);
        this.dispatchEvent(new DualSelectMoveSelectedEvent(this.moveable.sort()));
        this.dispatchEvent(new DualSelectUpdateEvent());
        // Necessary because updating a map won't trigger a state change
        this.requestUpdate();
    }

    @bound
    onMove(key: string) {
        this.toMove.delete(key);
        this.dispatchEvent(new DualSelectMoveRequestEvent("remove-one", key));
        this.requestUpdate();
    }

    override render() {
        return html`
            <div class="pf-c-dual-list-selector__menu">
                <ul class="pf-c-dual-list-selector__list">
                    ${map(this.selected, ([key, label]) => {
                        const selected = classMap({
                            "pf-m-selected": this.toMove.has(key),
                        });
                        return html` <li
                            class="pf-c-dual-list-selector__list-item"
                            aria-selected="false"
                            id="dual-list-selector-basic-selected-pane-list-option-0"
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
                                            >${label}</span
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

export default AkDualSelectSelectedPane;

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-selected-pane": AkDualSelectSelectedPane;
    }
}
