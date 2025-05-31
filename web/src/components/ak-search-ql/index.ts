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

    renderMenu() {
        if (!this.menuOpen || !this.ql) {
            return nothing;
        }
        return html`
            <div class="pf-c-search-input__menu">
                <ul class="pf-c-search-input__menu-list">
                    ${this.ql.suggestions.map((suggestion, idx) => {
                        return html`<li class="pf-c-search-input__menu-list-item">
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
