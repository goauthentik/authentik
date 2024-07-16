import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    EVENT_ADD_ALL,
    EVENT_ADD_SELECTED,
    EVENT_DELETE_ALL,
    EVENT_REMOVE_ALL,
    EVENT_REMOVE_SELECTED,
} from "../constants";

const styles = [
    PFBase,
    PFButton,
    css`
        :host {
            align-self: center;
            padding-right: var(--pf-c-dual-list-selector__controls--PaddingRight);
            padding-left: var(--pf-c-dual-list-selector__controls--PaddingLeft);
        }
        .pf-c-dual-list-selector {
            max-width: 4rem;
        }
        .ak-dual-list-selector__controls {
            display: grid;
            justify-content: center;
            align-content: center;
            height: 100%;
        }
    `,
];

/**
 * @element ak-dual-select-controls
 *
 * The "control box" for a dual-list multi-select. It's controlled by the parent orchestrator as to
 * whether or not any of its controls are enabled. It sends a variety of messages to the parent
 * orchestrator which will then reconcile the "available" and "selected" panes at need.
 *
 */

@customElement("ak-dual-select-controls")
export class AkDualSelectControls extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    /* Set to true if any *visible* elements can be added to the selected list
     */
    @property({ attribute: "add-active", type: Boolean })
    addActive = false;

    /* Set to true if any elements can be removed from the selected list (essentially,
     * if the selected list is not empty)
     */
    @property({ attribute: "remove-active", type: Boolean })
    removeActive = false;

    /* Set to true if *all* the currently visible elements can be moved
     * into the selected list (essentially, if any visible elements are
     * not currently selected)
     */
    @property({ attribute: "add-all-active", type: Boolean })
    addAllActive = false;

    /* Set to true if *any* of the elements currently visible in the available
     * pane are available to be moved to the selected list, enabling that
     * all of those specific elements be moved out of the selected list
     */
    @property({ attribute: "remove-all-active", type: Boolean })
    removeAllActive = false;

    /* if deleteAll is enabled, set to true to show that there are elements in the
     * selected list that can be deleted.
     */
    @property({ attribute: "delete-all-active", type: Boolean })
    enableDeleteAll = false;

    /* Set to true if you want the `...AllActive` buttons made available. */
    @property({ attribute: "enable-select-all", type: Boolean })
    selectAll = false;

    /* Set to true if you want the `ClearAllSelected` button made available */
    @property({ attribute: "enable-delete-all", type: Boolean })
    deleteAll = false;

    constructor() {
        super();
        this.onClick = this.onClick.bind(this);
    }

    onClick(eventName: string) {
        this.dispatchCustomEvent(eventName);
    }

    renderButton(label: string, event: string, active: boolean, direction: string) {
        return html`
            <div class="pf-c-dual-list-selector__controls-item">
                <button
                    ?aria-disabled=${!active}
                    ?disabled=${!active}
                    aria-label=${label}
                    class="pf-c-button pf-m-plain"
                    type="button"
                    @click=${() => this.onClick(event)}
                    data-ouia-component-type="AK/Button"
                >
                    <i class="fa ${direction}"></i>
                </button>
            </div>
        </div>`;
    }

    render() {
        return html`
            <div class="ak-dual-list-selector__controls">
                ${this.renderButton(
                    msg("Add"),
                    EVENT_ADD_SELECTED,
                    this.addActive,
                    "fa-angle-right",
                )}
                ${this.selectAll
                    ? html`
                          ${this.renderButton(
                              msg("Add All Available"),
                              EVENT_ADD_ALL,
                              this.addAllActive,
                              "fa-angle-double-right",
                          )}
                          ${this.renderButton(
                              msg("Remove All Available"),
                              EVENT_REMOVE_ALL,
                              this.removeAllActive,
                              "fa-angle-double-left",
                          )}
                      `
                    : nothing}
                ${this.renderButton(
                    msg("Remove"),
                    EVENT_REMOVE_SELECTED,
                    this.removeActive,
                    "fa-angle-left",
                )}
                ${this.deleteAll
                    ? html`${this.renderButton(
                          msg("Remove All"),
                          EVENT_DELETE_ALL,
                          this.enableDeleteAll,
                          "fa-times",
                      )}`
                    : nothing}
            </div>
        `;
    }
}

export default AkDualSelectControls;

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-controls": AkDualSelectControls;
    }
}
