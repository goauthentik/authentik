import { AKElement } from "@goauthentik/elements/Base";

import { TemplateResult } from "lit";
import { state } from "lit/decorators.js";

import { listStyles } from "./styles.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const styles = [PFBase, PFButton, PFDualListSelector, listStyles];

const hostAttributes = [
    ["aria-labelledby", "dual-list-selector-selected-pane-status"],
    ["aria-multiselectable", "true"],
    ["role", "listbox"],
];

/**
 * @element ak-dual-select-panel
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
export abstract class AkDualSelectAbstractPane extends AKElement {
    static get styles() {
        return styles;
    }

    /*
     * This is the only mutator for this object. It collects the list of objects the user has
     * clicked on *in this pane*. It is explicitly marked as "public" to emphasize that the parent
     * orchestrator for the dual-select widget can and will access it to get the list of keys to be
     * moved (removed) if the user so requests.
     *
     */
    @state()
    public toMove: Set<string> = new Set();

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

    move(key: string) {
        if (this.toMove.has(key)) {
            this.toMove.delete(key);
        } else {
            this.toMove.add(key);
        }
    }

    get moveable() {
        return Array.from(this.toMove.values());
    }

    abstract render(): TemplateResult;
}
