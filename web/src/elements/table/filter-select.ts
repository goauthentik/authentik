import { AKElement } from "#elements/Base";
import { RadioOption } from "#elements/forms/Radio";

import { Jsonifiable } from "type-fest";

import { PropertyValues } from "lit";
import { html, nothing } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { customElement, property } from "lit/decorators.js";

import PFSelect from "@patternfly/patternfly/components/Select/select.css";

/**
 * Select element specifically used for table filters.
 * @slot - Label of the filter element
 * @event {change} - Event fired when a selection is made
 */
@customElement("ak-table-filter-select")
export class FilterSelect<T extends Jsonifiable> extends AKElement {
    static styles = [PFSelect];

    @property({ type: Boolean, reflect: true })
    open = false;

    @property({ type: Array })
    options: RadioOption<T>[] = [];

    @property({ attribute: false })
    selectedOption?: RadioOption<T>;

    @property({ attribute: false })
    value: T | null = null;

    protected updated(changedProperties: PropertyValues): void {
        if (changedProperties.has("value") && this.options.length > 0) {
            const selected = this.options.filter((opt) => opt.value === this.value);
            if (selected.length > 0) {
                this.selectedOption = selected[0];
            }
        }
    }

    renderMenu() {
        if (!this.open) return nothing;
        return html`<ul class="pf-c-select__menu" role="listbox">
            ${this.options.map((opt) => {
                return html`<li role="presentation" class="pf-c-select__menu-wrapper">
                    <button
                        class="pf-c-select__menu-item"
                        role="option"
                        type="button"
                        @click=${() => {
                            this.selectedOption = opt;
                            this.dispatchEvent(
                                new CustomEvent("change", {
                                    detail: opt,
                                }),
                            );
                            this.open = false;
                        }}
                    >
                        <span class="pf-c-select__menu-item-main">${opt.label}</span>
                        ${opt.description
                            ? html`<span class="pf-c-select__menu-item-description">
                                  ${opt.description}
                              </span>`
                            : nothing}
                    </button>
                </li>`;
            })}
        </ul>`;
    }

    render() {
        return html`<div class=${classMap({ "pf-c-select": true, "pf-m-expanded": this.open })}>
            <button
                type="button"
                class="pf-c-select__toggle"
                @click=${() => {
                    this.open = !this.open;
                }}
            >
                <div class="pf-c-select__toggle-wrapper">
                    <span class="pf-c-select__toggle-text">
                        <i class="fa fa-filter" aria-hidden="true"></i>
                        ${this.selectedOption
                            ? html`${this.selectedOption.label}`
                            : html`<slot></slot>`}
                    </span>
                </div>
                <span class="pf-c-select__toggle-arrow">
                    <i class="fas fa-caret-down" aria-hidden="true"></i>
                </span>
            </button>
            ${this.renderMenu()}
        </div>`;
    }
}
