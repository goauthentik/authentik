import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const styles = [PFBase, PFButton, PFDualListSelector];

@customElement("ak-dual-select-controls")
export class AkDualSelectControls extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    @property({ attribute: "add-active", type: Boolean })
    addActive = false;

    @property({ attribute: "remove-active", type: Boolean })
    removeActive = false;

    @property({ attribute: "add-all-active", type: Boolean })
    addAllActive = false;

    @property({ attribute: "remove-all-active", type: Boolean })
    removeAllActive = false;

    @property({ attribute: "disabled", type: Boolean })
    disabled = false;

    @property({ attribute: "enable-select-all", type: Boolean })
    selectAll = false;

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
                    ?aria-disabled=${this.disabled || !active}
                    ?disabled=${this.disabled || !active}
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
        // prettier-ignore
        return html`
            <div class="pf-c-dual-list-selector">
                <div class="pf-c-dual-list-selector__controls">
                    ${this.renderButton(msg("Add"), "ak-dual-select-add", this.addActive, "fa-angle-right")}
                    ${this.selectAll
                        ? html`
                              ${this.renderButton(msg("Add All"), "ak-dual-select-add-all", this.addAllActive, "fa-angle-double-right")}
                              ${this.renderButton(msg("Remove All"), "ak-dual-select-remove-all", this.removeAllActive, "fa-angle-double-left")}
                          `
                        : nothing}
                    ${this.renderButton(msg("Remove"), "ak-dual-select-remove", this.removeActive, "fa-angle-left")}
                </div>
            </div>
        `;
    }
}

export default AkDualSelectControls;
