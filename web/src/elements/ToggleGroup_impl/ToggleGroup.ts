/**
 * @file Implementation code for the ToggleGroup component
 */

import Styles from "./ToggleGroup.styles";

import { FormAssociatedElement } from "#elements/forms/form-associated-element";

import { html, nothing, PropertyValues } from "lit";
import { property } from "lit/decorators.js";
import { ref } from "lit/directives/ref.js";

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
 * @fires ak-toggle - Fired when someone clicks on a toggle option. Carries the value of the option.
 * @element ak-toggle-group
 */

export class ToggleGroup extends FormAssociatedElement<string> {
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
        return Array.from(this.rawOptions).map((option: HTMLOptionElement): Option => [
            option.getAttribute("value") ?? "",
            option.textContent ?? "",
            { disabled: option.hasAttribute("disabled") },
        ]);
    }

    get values(): Set<string> {
        return new Set(this.multi ? this.value.split(this.separator) : [this.value]);
    }

    public toJSON(): string {
        return this.value;
    }

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("value") || changed.has("required")) {
            this.setFormValue(this.value);
        }
    }

    protected handleClick = (ev: EventTarget | null) => {
        if (!(ev && ev instanceof HTMLElement)) {
            return;
        }

        const value = ev.closest("button")?.dataset.value;

        if (value === undefined) {
            return;
        }

        if (!this.multi) {
            this.value = value;
        }

        this.dispatchEvent(new ToggleGroupEvent(value));
    };

    render() {
        const values = this.values;

        return html` <div part="toggle-group" @click=${(ev: Event) => this.handleClick(ev.target)}>
            ${this.options.map(
                ([key, label, { disabled }], index) =>
                    html`<div part="item">
                        <button
                            ${index === 0 ? ref(this.anchorRef) : nothing}
                            part="button${values.has(key) ? " selected" : ""}"
                            aria-pressed=${values.has(key) ? "true" : "false"}
                            ?disabled=${disabled}
                            type="button"
                            data-value=${key}
                        >
                            <span part="label">${label}</span>
                        </button>
                    </div> `,
            )}
        </div>`;
    }

    public override firstUpdated(changed: PropertyValues<this>) {
        super.firstUpdated(changed);
        this.role = this.role ?? "group";
    }
}

export default ToggleGroup;
