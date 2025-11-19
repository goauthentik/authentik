import { AKElement } from "#elements/Base";
import { CustomEmitterElement } from "#elements/utils/eventEmitter";

import Styles from "#components/ak-toggle-group.css";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFToggleGroup from "@patternfly/patternfly/components/ToggleGroup/toggle-group.css";

type Pair = [string, string];

/**
 * Toggle Group
 *
 * An implementation of the Patternfly Toggle Group as a LitElement
 *
 * @element ak-toggle-group
 *
 * @fires ak-toggle - Fired when someone clicks on a toggle option. Carries the value of the option.
 */

// MYNIS:
// A 'name' property so that the event carries *which* toggle group emitted the event.

@customElement("ak-toggle-group")
export class AkToggleGroup extends CustomEmitterElement(AKElement) {
    static styles = [PFToggleGroup, Styles];

    /**
     * The value (causes highlighting, value is returned)
     *
     * @attr
     */
    @property({ type: String, reflect: true })
    value = "";

    get rawOptions(): HTMLOptionElement[] {
        return Array.from(this.querySelectorAll("option") ?? []);
    }

    get options(): Pair[] {
        return Array.from(this.rawOptions).map(
            (option: HTMLOptionElement): Pair => [
                option.getAttribute("value") ?? "",
                option.textContent ?? "",
            ],
        );
    }

    render() {
        const last = this.options.length - 1;
        const mkClass = (v: string) => ({
            "pf-c-toggle-group__button": true,
            "pf-m-selected": this.value === v,
        });

        const mkClick = (v: string) => () => {
            this.dispatchCustomEvent("ak-toggle", { value: v });
        };

        return html` <div class="pf-c-toggle-group">
            ${this.options.map(
                ([key, label], idx) =>
                    html`<div class="pf-c-toggle-group__item">
                            <button
                                class="${classMap(mkClass(key))}"
                                type="button"
                                @click=${mkClick(key)}
                            >
                                <span class="pf-c-toggle-group__text">${label}</span>
                            </button>
                        </div>
                        ${idx < last
                            ? html`<div class="pf-c-divider pf-m-vertical" role="separator"></div>`
                            : nothing} `,
            )}
        </div>`;
    }
}

export default AkToggleGroup;

declare global {
    interface HTMLElementTagNameMap {
        "ak-toggle-group": AkToggleGroup;
    }
}
