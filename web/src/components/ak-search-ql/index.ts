import "#elements/buttons/Dropdown";

import { AKElement } from "#elements/Base";
import { PaginatedResponse } from "#elements/table/Table";

import DjangoQL, { Introspections } from "@mrmarble/djangoql-completion";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
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

    @state()
    cursorX: number = 0;

    @state()
    cursorY: number = 0;

    ql?: QL;
    canvas?: CanvasRenderingContext2D;

    set apiResponse(value: PaginatedResponse<unknown> | undefined) {
        if (!value || !value.autocomplete || !this.ql) {
            return;
        }
        this.ql.loadIntrospections(value.autocomplete as unknown as Introspections);
    }

    public static styles: CSSResult[] = [
        PFBase,
        PFFormControl,
        PFSearchInput,
        css`
            ::-webkit-search-cancel-button {
                display: none;
            }
            .ql.pf-c-form-control {
                font-family: monospace;
                resize: vertical;
                height: 2.25em;
            }
            .selected {
                background-color: var(--pf-c-search-input__menu-item--hover--BackgroundColor);
            }
            :host([theme="dark"]) .pf-c-search-input__menu {
                --pf-c-search-input__menu--BackgroundColor: var(--ak-dark-background-light-ish);
                color: var(--ak-dark-foreground);
            }
            :host([theme="dark"]) .pf-c-search-input__menu-item {
                --pf-c-search-input__menu-item--Color: var(--ak-dark-foreground);
            }
            :host([theme="dark"]) .pf-c-search-input__menu-item:hover {
                --pf-c-search-input__menu-item--BackgroundColor: var(--ak-dark-background-lighter);
            }
            :host([theme="dark"]) .pf-c-search-input__menu-list-item.selected {
                --pf-c-search-input__menu-item--hover--BackgroundColor: var(
                    --ak-dark-background-light
                );
            }
            :host([theme="dark"]) .pf-c-search-input__text::before {
                border: 0;
            }
            .pf-c-search-input__menu {
                position: fixed;
                min-width: 0;
            }
        `,
    ];

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
        });
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        if (!context) {
            console.error("authentik/ql: failed to get canvas context");
            return;
        }
        context.font = window.getComputedStyle(this.searchElement).font;
        this.canvas = context;
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
        this.updateDropdownPosition();
        this.requestUpdate();
    }

    updateDropdownPosition() {
        if (!this.searchElement) {
            return;
        }
        const bcr = this.getBoundingClientRect();
        // We need the width of a letter to measure x; we use a monospaced font but still
        // check the length for `m` as its the widest ASCII char
        const metrics = this.canvas?.measureText("m");
        const letterWidth = Math.ceil(metrics?.width || 0) + 1;

        // Mostly static variables for padding, font line-height and how many
        const lineHeight = parseInt(window.getComputedStyle(this.searchElement).lineHeight, 10);
        const paddingTop = parseInt(window.getComputedStyle(this.searchElement).paddingTop, 10);
        const paddingLeft = parseInt(window.getComputedStyle(this.searchElement).paddingLeft, 10);
        const paddingRight = parseInt(window.getComputedStyle(this.searchElement).paddingRight, 10);
        const actualInnerWidth = bcr.width - paddingLeft - paddingRight;

        let relX = 0;
        let relY = 1;
        let letterIndex = 0;

        this.searchElement.value.split(" ").some((word, idx) => {
            letterIndex += word.length;
            const newRelX = relX + word.length * letterWidth;
            if (newRelX > actualInnerWidth) {
                relY += 1;
                if (letterIndex > this.searchElement!.selectionStart) {
                    relX =
                        letterWidth * word.length -
                        (letterIndex - this.searchElement!.selectionStart) * letterWidth;
                    return true;
                }
                relX = word.length * letterWidth;
            } else {
                relX = newRelX + 1;
            }
        });

        this.cursorX = bcr.x + paddingLeft + relX;
        this.cursorY = bcr.y + paddingTop + relY * lineHeight;
    }

    onKeyDown(ev: KeyboardEvent) {
        this.updateDropdownPosition();
        if (ev.key === "Enter" && ev.metaKey && this.onSearch && this.searchElement) {
            this.onSearch(this.searchElement?.value);
            return;
        }
        if (!this.menuOpen) return;
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
                if (this.selected !== undefined) {
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

    protected renderMenu() {
        if (!this.menuOpen || !this.ql) {
            return nothing;
        }
        return html`
            <div
                class="pf-c-search-input__menu"
                style="left: ${this.cursorX}px; top: ${this.cursorY}px;"
            >
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

    public render(): TemplateResult {
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
