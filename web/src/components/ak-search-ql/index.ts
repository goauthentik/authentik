import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/buttons/Dropdown";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import DjangoQL from "@mrmarble/djangoql-completion";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSearchInput from "@patternfly/patternfly/components/SearchInput/search-input.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export class QL extends DjangoQL {
    createCompletionElement() {
        this.completionEnabled = !!this.options.completionEnabled;
        return;
    }
    logError(message: string): void {
        console.warn(`authentik/ql: ${message}`);
    }
    textareaResize() {}
}

@customElement("ak-search-ql")
export class QLSearch extends AKElement {
    @property()
    value?: string;

    @query("[name=search]")
    searchElement?: HTMLTextAreaElement;

    @state()
    menuOpen = false;

    @property()
    onSearch?: (value: string) => void;

    @state()
    selected?: number;

    ql?: QL;

    set apiResponse(value: PaginatedResponse<unknown> | undefined) {
        if (!value || !value.autocomplete || !this.ql) {
            return;
        }
        this.ql.loadIntrospections(value.autocomplete);
    }

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFFormControl,
            PFSearchInput,
            css`
                ::-webkit-search-cancel-button {
                    display: none;
                }
                .ql.pf-c-form-control {
                    font-family: monospace;
                }
                :host([theme="dark"]) .pf-c-search-input__text::before {
                    border: 0;
                }
                .selected {
                    background-color: gray;
                }
            `,
        ];
    }

    firstUpdated() {
        if (!this.searchElement) {
            return;
        }
        this.ql = new QL({
            completionEnabled: true,
            introspections: {
                current_model: "",
                models: {},
            },
            selector: this.searchElement,
            autoResize: false,
            onSubmit: (value: string) => {
                if (!this.onSearch) return;
                this.onSearch(value);
            },
        });
    }

    refreshCompletions() {
        this.value = this.searchElement?.value;
        if (!this.ql) {
            return;
        }
        this.ql.generateSuggestions();
        if (this.ql.suggestions.length < 1 || this.ql.loading) {
            this.menuOpen = false;
            return;
        }
        this.menuOpen = true;
        this.requestUpdate();
    }

    onKeyDown(ev: KeyboardEvent) {
        switch (ev.key) {
            case "ArrowUp":
                if (this.ql?.suggestions.length) {
                    if (this.selected === undefined) {
                        this.selected = this.ql?.suggestions.length - 1;
                    } else if (this.selected === 0) {
                        this.selected = undefined;
                    } else {
                        this.selected -= 1;
                    }
                    this.refreshCompletions();
                    ev.preventDefault();
                }
                break;
            case "ArrowDown":
                if (this.ql?.suggestions.length) {
                    if (this.selected === undefined) {
                        this.selected = 0;
                    } else if (this.selected < this.ql?.suggestions.length - 1) {
                        this.selected += 1;
                    } else {
                        this.selected = undefined;
                    }
                    this.refreshCompletions();
                    ev.preventDefault();
                }
                break;
            case "Tab":
                if (this.selected) {
                    this.ql?.selectCompletion(this.selected);
                    ev.preventDefault();
                }
                break;
            case "Enter":
                // Technically this is a textarea, due to automatic multi-line feature,
                // but other than that it should look and behave like a normal input.
                // So expected behavior when pressing Enter is to submit the form,
                // not to add a new line.
                if (this.selected!== undefined) {
                    this.ql?.selectCompletion(this.selected);
                }
                ev.preventDefault();
                break;
            case "Escape":
                this.menuOpen = false;
                break;
            case "Shift": // Shift
            case "Control": // Ctrl
            case "Alt": // Alt
            case "Meta": // Windows Key or Cmd on Mac
                // Control keys shouldn't trigger completion popup
                break;
        }
    }

    renderMenu() {
        if (!this.menuOpen || !this.ql) {
            return nothing;
        }
        return html`
            <div class="pf-c-search-input__menu">
                <ul class="pf-c-search-input__menu-list">
                    ${this.ql.suggestions.map((suggestion, idx) => {
                        return html`<li
                            class="pf-c-search-input__menu-list-item ${this.selected === idx
                                ? "selected"
                                : ""}"
                        >
                            <button
                                class="pf-c-search-input__menu-item"
                                type="button"
                                @click=${() => {
                                    this.ql?.selectCompletion(idx);
                                    this.refreshCompletions();
                                }}
                            >
                                <span class="pf-c-search-input__menu-item-text"
                                    >${suggestion.text}</span
                                >
                            </button>
                        </li>`;
                    })}
                </ul>
            </div>
        `;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-search-input">
            <div class="pf-c-search-input__bar">
                <span class="pf-c-search-input__text">
                    <textarea
                        class="pf-c-form-control ql"
                        name="search"
                        placeholder=${msg("Search...")}
                        spellcheck="false"
                        @input=${(ev: InputEvent) => this.refreshCompletions()}
                        @keydown=${this.onKeyDown}
                    >
${ifDefined(this.value)}</textarea
                    >
                </span>
            </div>
            ${this.renderMenu()}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-ql": QLSearch;
    }
}
