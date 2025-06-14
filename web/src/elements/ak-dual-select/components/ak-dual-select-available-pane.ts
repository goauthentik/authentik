import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { PropertyValues, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";
import { createRef, ref } from "lit/directives/ref.js";

import { availablePaneStyles, listStyles } from "./styles.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { DualSelectEventType, DualSelectPair } from "../types.js";

const hostAttributes = [
    ["aria-labelledby", "dual-list-selector-available-pane-status"],
    ["aria-multiselectable", "true"],
    ["role", "listbox"],
] as const satisfies Array<[string, string]>;

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
 */
@customElement("ak-dual-select-available-pane")
export class AkDualSelectAvailablePane extends CustomEmitterElement<DualSelectEventType>(
    AKElement,
) {
    static styles = [PFBase, PFButton, PFDualListSelector, listStyles, availablePaneStyles];

    //#region Properties

    /* The array of key/value pairs this pane is currently showing */
    @property({ type: Array })
    readonly options: DualSelectPair[] = [];

    /**
     * A set (set being easy for lookups) of keys with all the pairs selected,
     * so that the ones currently being shown that have already been selected
     * can be marked and their clicks ignored.
     */
    @property({ type: Object })
    readonly selected: Set<string> = new Set();

    //#endregion

    //#region State

    /**
     * This is the only mutator for this object.
     * It collects the list of objects the user has clicked on *in this pane*.
     *
     * It is explicitly marked as "public" to emphasize that the parent orchestrator
     * for the dual-select widget can and will access it to get the list of keys to be
     * moved (removed) if the user so requests.
     */
    @state()
    public toMove: Set<string> = new Set();

    //#endregion

    //#region Refs

    protected listRef = createRef<HTMLDivElement>();

    //#region Lifecycle

    connectedCallback() {
        super.connectedCallback();

        for (const [attr, value] of hostAttributes) {
            if (!this.hasAttribute(attr)) {
                this.setAttribute(attr, value);
            }
        }
    }

    protected updated(changed: PropertyValues<this>) {
        if (changed.has("options")) {
            this.listRef.value?.scrollTo(0, 0);
        }
    }

    //#region Public API

    public clearMove() {
        this.toMove = new Set();
    }

    get moveable() {
        return Array.from(this.toMove.values());
    }

    //#endregion

    //#region Event Listeners

    #clickListener(key: string): void {
        if (this.selected.has(key)) return;

        if (this.toMove.has(key)) {
            this.toMove.delete(key);
        } else {
            this.toMove.add(key);
        }

        this.dispatchCustomEvent(
            DualSelectEventType.MoveChanged,
            Array.from(this.toMove.values()).sort(),
        );

        this.dispatchCustomEvent(DualSelectEventType.Move);

        // Necessary because updating a map won't trigger a state change
        this.requestUpdate();
    }

    #moveListener(key: string): void {
        this.toMove.delete(key);

        this.dispatchCustomEvent(DualSelectEventType.AddOne, key);
        this.requestUpdate();
    }

    //#region Render

    // DO NOT use `Array.map()` instead of Lit's `map()` function. Lit's `map()` is object-aware and
    // will not re-arrange or reconstruct the list automatically if the actual sources do not
    // change; this allows the available pane to illustrate selected items with the checkmark
    // without causing the list to scroll back up to the top.

    render() {
        return html`
            <div ${ref(this.listRef)} class="pf-c-dual-list-selector__menu">
                <ul class="pf-c-dual-list-selector__list">
                    ${map(this.options, ([key, label]) => {
                        const selected = classMap({
                            "pf-m-selected": this.toMove.has(key),
                        });

                        return html` <li
                            class="pf-c-dual-list-selector__list-item"
                            aria-selected="false"
                            @click=${() => this.#clickListener(key)}
                            @dblclick=${() => this.#moveListener(key)}
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

    //#endregion
}

export default AkDualSelectAvailablePane;

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-available-pane": AkDualSelectAvailablePane;
    }
}
