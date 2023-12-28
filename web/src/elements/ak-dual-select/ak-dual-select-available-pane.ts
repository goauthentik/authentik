import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { DualSelectPair } from "./types";

const styles = [
    PFBase,
    PFButton,
    PFDualListSelector,
    css`
        .pf-c-dual-list-selector__item {
            padding: 0.25rem;
        }
        .pf-c-dual-list-selector__item-text i {
            display: inline-block;
            margin-left: 0.5rem;
            font-weight: 200;
            color: var(--pf-global--palette--black-500);
            font-size: var(--pf-global--FontSize--xs);
        }
    `,
];

const hostAttributes = [
    ["aria-labelledby", "dual-list-selector-available-pane-status"],
    ["aria-multiselectable", "true"],
    ["role", "listbox"],
];

@customElement("ak-dual-select-available-pane")
export class AkDualSelectAvailablePane extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    @property({ type: Array })
    options: DualSelectPair[] = [];

    @property({ attribute: "to-move", type: Object })
    toMove: Set<string> = new Set();

    @property({ attribute: "selected", type: Object })
    selected: Set<string> = new Set();

    @property({ attribute: "disabled", type: Boolean })
    disabled = false;

    constructor() {
        super();
        this.onClick = this.onClick.bind(this);
    }

    onClick(key: string) {
        if (this.selected.has(key)) {
            // An already selected item cannot be moved into the "selected" category
            return;
        }
        if (this.toMove.has(key)) {
            this.toMove.delete(key);
        } else {
            this.toMove.add(key);
        }
        this.requestUpdate(); // Necessary because updating a map won't trigger a state change
        this.dispatchCustomEvent("ak-dual-select-move-changed", Array.from(this.toMove.keys()));
    }

    connectedCallback() {
        super.connectedCallback();
        hostAttributes.forEach(([attr, value]) => {
            if (!this.hasAttribute(attr)) {
                this.setAttribute(attr, value);
            }
        });
    }

    render() {
        return html`
            <div class="pf-c-dual-list-selector">
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
                                role="option"
                                tabindex="-1"
                            >
                                <div class="pf-c-dual-list-selector__list-item-row ${selected}">
                                    <span class="pf-c-dual-list-selector__item">
                                        <span class="pf-c-dual-list-selector__item-main">
                                            <span class="pf-c-dual-list-selector__item-text"
                                                >${label}${this.selected.has(key)
                                                    ? html`<i class="fa fa-check"></i>`
                                                    : nothing}</span
                                            ></span
                                        ></span
                                    >
                                </div>
                            </li>`;
                        })}
                    </ul>
                </div>
            </div>
        `;
    }
}

export default AkDualSelectAvailablePane;
