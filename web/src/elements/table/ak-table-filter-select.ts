import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { Jsonifiable } from "type-fest";

import { PropertyValues } from "lit";
import { html, nothing } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { customElement, property } from "lit/decorators.js";

import PFSelect from "@patternfly/patternfly/components/Select/select.css";

export interface FilterOption<T extends Jsonifiable | undefined> {
    label: string;
    description?: SlottedTemplateResult;
    default?: boolean;
    value: T;
    disabled?: boolean;
}

/**
 * Select element specifically used for table filters.
 * @slot - Label of the filter element
 * @event {change} - Event fired when a selection is made
 */
@customElement("ak-table-filter-select")
export class TableFilterSelect<T extends Jsonifiable> extends AKElement {
    static styles = [PFSelect];

    @property({ type: Boolean, reflect: true })
    open = false;

    @property({ type: Array })
    options: FilterOption<T>[] = [];

    @property({ attribute: false })
    selectedOption?: FilterOption<T>;

    @property()
    group?: string;

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

    renderOption(opt: FilterOption<T>): SlottedTemplateResult {
        const inner = html`${opt.label}
        ${this.selectedOption?.value === opt.value
            ? html`<span class="pf-c-select__menu-item-icon">
                  <i class="fa fa-check"></i>
              </span>`
            : nothing}`;
        return html`<li role="presentation" class="pf-c-select__menu-wrapper">
            <button
                class=${classMap({
                    "pf-c-select__menu-item": true,
                    "pf-m-selected": this.selectedOption?.value === opt.value,
                    "pf-m-description": !!opt.description,
                })}
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
                ${opt.description
                    ? html`<span class="pf-c-select__menu-item-main">${inner}</span>
                          <span class="pf-c-select__menu-item-description">
                              ${opt.description}
                          </span>`
                    : inner}
            </button>
        </li>`;
    }

    renderMenu(): SlottedTemplateResult {
        if (!this.open) return nothing;
        return html`<div class="pf-c-select__menu">
            <div class="pf-c-select__menu-group">
                <div class="pf-c-select__menu-group-title" id="Status" aria-hidden="true">
                    ${this.group}
                </div>
                <ul role="listbox">
                    ${this.options.map((opt) => this.renderOption(opt))}
                </ul>
            </div>
        </div>`;
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-filter-select": TableFilterSelect<Jsonifiable>;
    }
}
