import { AKElement } from "@goauthentik/elements/Base";

import { css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export type SelectPair = [string, string | TemplateResult];

// Group key, key and label.
export type SelectGroup = [string | undefined, SelectPair[]];

const isSelectPair = (v: SelectGroup | SelectPair): v is SelectPair => !Array.isArray(v[1]);

const fixLabel = (label: string | TemplateResult) =>
    typeof label !== "string"
        ? label
        : html`<div class="pf-c-dropdown__menu-item-main">${label}</div>`;

// The "active" color: --pf-v5-global--palette--blue-50
// The "hover" color: --pf-v5-global--BackgroundColor--100

@customElement("ak-select-menu")
export class AkSelectMenu extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFSelect,
            PFDropdown,
            css`
                #ak-select-menu {
                    position: fixed;
                    inset: 0 auto auto 0;
                    width: 100%;
                }
                #ak-select-menu-list {
                    max-height: 50vh;
                    min-width: 320px;
                    width: 25vw;
                    overflow-y: auto;
                }

                /* These are supplied by pf-select, but not by pf-dropdown, dammit. */
                .pf-m-selected {
                    background-color: var(--pf-global--palette--blue-50);
                }

                .pf-m-selected:hover {
                    background-color: var(--pf-global--palette--blue-100);
                }
            `,
        ];
    }

    // The objects currently available under search
    @property({ attribute: false })
    options: SelectPair[] | SelectGroup[] = [];

    @property({ attribute: true })
    value?: string;

    @property({ type: Boolean })
    required = false;

    // A textual string representing "The user has affirmed they want to leave the selection blank."
    // Only used if `required` above is false;
    @property()
    emptyOption = "---------";

    oneOption([key, label]: SelectPair, index: number) {
        const extraClasses = { "pf-m-selected": key === this.value };
        key === this.value && console.log("KEY:", key);

        return html` <li>
            <button
                class="pf-c-dropdown__menu-item ${classMap(extraClasses)}"
                role="option"
                value=${key}
                tabindex=${index}
            >
                ${fixLabel(label)}
            </button>
        </li>`;
    }

    oneOptionGroup([group, options]: SelectGroup) {
        return html`<section class="pf-c-dropdown__group">
            <h1 class="pf-c-dropdown__group-title">${group}</h1>
            <ul>
                ${map(options, (opt) => this.oneOption(opt))}
            </ul>
        </section>`;
    }

    renderGroupedMenu(options: SelectGroup[]) {
        return html`${map(options, (option) => this.oneOptionGroup(option))}`;
    }

    renderFlatMenu(options: SelectPair[]) {
        return html`<ul>
            ${map(options, (option) => this.oneOption(option))}
        </ul>`;
    }

    renderItems() {
        return isSelectPair(this.options[0])
            ? this.renderFlatMenu(this.options)
            : this.renderGroupedMenu(this.options);
    }

    renderEmptyMenuItem() {
        return html`<li class="ak-c-dropdown-control">
            <button
                class="pf-c-dropdown__menu-item"
                role="option"
                data-menu-empty-item="true"
                tabindex="0"
            >
                ${this.emptyOption}
            </button>
        </li>`;
    }

    render() {
        console.log(this.value);
        return html`<div id="ak-select-menu" class="pf-c-dropdown pf-m-expanded">
            <ul
                id="ak-select-menu-list"
                class="pf-c-dropdown__menu pf-m-static"
                role="listbox"
                tabindex="0"
            >
                ${this.required ? nothing : this.renderEmptyMenuItem()} ${this.renderItems()}
            </ul>
        </div>`;
    }
}
