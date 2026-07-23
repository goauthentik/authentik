/**
 * @file Implementation code for the ToggleGroup component
 */

import Styles from "./ToggleGroup.styles";

import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

type Option = [string, string, { disabled?: boolean }];

export class ToggleGroupEvent<T = string> extends Event {
    static readonly eventName = "ak-toggle";
    public value: T;
    constructor(value: T) {
        super(ToggleGroupEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * Toggle Group
 *
 * An implementation of the Patternfly Toggle Group as a LitElement. This component is not intended
 * to be used as a control. If you need that, use RadioGroup.
 *
 * @element ak-toggle-group
 *
 * @fires ak-toggle - Fired when someone clicks on a toggle option. Carries the value of the option.
 */

export class ToggleGroup extends LitElement {
    static styles = [Styles];

    /**
     * The value (causes highlighting, value is returned)
     *
     * @attr
     */

    @property({ type: String })
    value = "";

    @property({ type: Boolean, reflect: true })
    multi = false;

    @property({ type: String })
    separator = ",";

    protected optionsObserver: MutationObserver | null = null;

    public connectedCallback() {
        super.connectedCallback();
        this.optionsObserver = new MutationObserver((_mutations) => {
            requestAnimationFrame(() => this.requestUpdate());
        });
        this.optionsObserver.observe(this, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["value", "disabled"],
            characterData: true, // Watch for label changes, too.
        });
    }

    public disconnectedCallback() {
        super.disconnectedCallback();
        this.optionsObserver?.disconnect();
        this.optionsObserver = null;
    }

    get rawOptions(): HTMLOptionElement[] {
        return Array.from(this.querySelectorAll("option") ?? []);
    }

    get options(): Option[] {
        return Array.from(this.rawOptions).map(
            (option: HTMLOptionElement): Option => [
                option.getAttribute("value") ?? "",
                option.textContent ?? "",
                { disabled: option.hasAttribute("disabled") },
            ],
        );
    }

    get values(): Set<string> {
        return new Set(this.multi ? this.value.split(this.separator) : [this.value]);
    }

    render() {
        const values = this.values;
        const mkClick = (v: string) => () => {
            this.dispatchEvent(new ToggleGroupEvent(v));
        };

        return html` <div role=${this.multi ? "group" : "radiogroup"} part="toggle-group">
            ${this.options.map(
                ([key, label, { disabled }]) =>
                    html`<div part="item">
                        <button
                            part="button${values.has(key) ? " selected" : ""}"
                            aria-pressed=${values.has(key) ? "true" : "false"}
                            ?disabled=${disabled}
                            type="button"
                            @click=${mkClick(key)}
                        >
                            <span part="label">${label}</span>
                        </button>
                    </div> `,
            )}
        </div>`;
    }
}

export default ToggleGroup;
