import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { listStyles, selectedPaneStyles } from "./styles.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EVENT_REMOVE_ONE } from "../constants";
import type { DualSelectPair } from "../types";

const styles = [PFBase, PFButton, PFDualListSelector, listStyles, selectedPaneStyles];

const hostAttributes = [
    ["aria-labelledby", "dual-list-selector-selected-pane-status"],
    ["aria-multiselectable", "true"],
    ["role", "listbox"],
];

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
export class AkDualSelectSelectedPane extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    /* The array of key/value pairs that are in the selected list.  ALL of them. */
    @property({ type: Array })
    readonly selected: DualSelectPair[] = [];

    /*
     * This is the only mutator for this object. It collects the list of objects the user has
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
        if (this.toMove.has(key)) {
            this.toMove.delete(key);
        } else {
            this.toMove.add(key);
        }
        this.dispatchCustomEvent(
            "ak-dual-select-selected-move-changed",
            Array.from(this.toMove.values()).sort(),
        );
        this.dispatchCustomEvent("ak-dual-select-move");
        // Necessary because updating a map won't trigger a state change
        this.requestUpdate();
    }

    onMove(key: string) {
        this.toMove.delete(key);
        this.dispatchCustomEvent(EVENT_REMOVE_ONE, key);
        this.requestUpdate();
    }

    get moveable() {
        return Array.from(this.toMove.values());
    }

    render() {
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
