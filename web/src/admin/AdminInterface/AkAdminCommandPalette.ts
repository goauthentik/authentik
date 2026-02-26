import type { CommandPaletteAction } from "./AdminCommandPalette.js";

import { AKElement } from "#elements/Base";

import Styles from "#admin/AdminInterface/AkAdminCommandPalette.css" with { type: "bundled-text" };

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

@customElement("ak-admin-command-palette")
export class AkAdminCommandPalette extends AKElement {
    public static readonly styles: CSSResult[] = [Styles];

    @property({ type: Array })
    public actions: CommandPaletteAction[] = [];

    @state()
    private _open = false;

    @state()
    private _query = "";

    @state()
    private _selectedIndex = 0;

    @query("input")
    private _input?: HTMLInputElement;

    @query("dialog")
    private _dialog?: HTMLDialogElement;

    #abortController?: AbortController;

    public connectedCallback(): void {
        super.connectedCallback();

        this.#abortController = new AbortController();
        const { signal } = this.#abortController;

        window.addEventListener(
            "keydown",
            (event: KeyboardEvent) => {
                if ((event.metaKey || event.ctrlKey) && event.key === "k") {
                    event.preventDefault();
                    this._open = !this._open;
                }
            },
            { signal },
        );
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#abortController?.abort();
    }

    public override willUpdate(changed: PropertyValues): void {
        super.willUpdate(changed);

        if (changed.has("_open") && this._open) {
            this._query = "";
            this._selectedIndex = 0;
        }

        if (this._selectedIndex >= this.filteredActions.length) {
            this._selectedIndex = Math.max(this.filteredActions.length - 1, 0);
        }
    }

    public override updated(changed: PropertyValues): void {
        super.updated(changed);

        if (!changed.has("_open")) return;

        if (this._open) {
            this._dialog?.showModal();
            this._input?.focus();
        } else if (this._dialog?.open) {
            this._dialog.close();
        }
    }

    get filteredActions(): CommandPaletteAction[] {
        if (!this._query) return this.actions;
        const q = this._query.toLowerCase();
        return this.actions.filter(
            (a) => a.title.toLowerCase().includes(q) || a.section?.toLowerCase().includes(q),
        );
    }

    #handleKeydown = (event: KeyboardEvent) => {
        const items = this.filteredActions;

        switch (event.key) {
            case "ArrowDown": {
                event.preventDefault();
                if (items.length === 0) {
                    this._selectedIndex = 0;
                    break;
                }
                this._selectedIndex = Math.min(this._selectedIndex + 1, items.length - 1);
                this.#scrollSelectedIntoView();
                break;
            }
            case "ArrowUp": {
                event.preventDefault();
                if (items.length === 0) {
                    this._selectedIndex = 0;
                    break;
                }
                this._selectedIndex = Math.max(this._selectedIndex - 1, 0);
                this.#scrollSelectedIntoView();
                break;
            }
            case "Enter": {
                event.preventDefault();
                const action = items[this._selectedIndex];
                if (action) {
                    action.handler();
                    this._open = false;
                }
                break;
            }
        }
    };

    #scrollSelectedIntoView() {
        this.updateComplete.then(() => {
            const selected = this.renderRoot.querySelector(".action.is-selected");
            selected?.scrollIntoView({ block: "nearest" });
        });
    }

    get #openHotkeyLabel(): string {
        const platform = globalThis.navigator?.platform ?? "";
        return /Mac|iPhone|iPad/.test(platform) ? "⌘ K" : "Ctrl K";
    }

    #handleInput = (event: Event) => {
        this._query = (event.target as HTMLInputElement).value;
        this._selectedIndex = 0;
    };

    #actionOptionId(index: number): string {
        return `ak-admin-command-option-${index}`;
    }

    // Clicking on the <dialog> element itself means the backdrop was clicked
    #handleDialogClick = (event: MouseEvent) => {
        if (event.target === this._dialog) {
            this._open = false;
        }
    };

    #renderActions() {
        const items = this.filteredActions;

        if (items.length === 0) {
            const emptyDescription = this._query
                ? msg("Try a different keyword or clear your search.")
                : msg("Start typing to search admin pages and commands.");

            return html`<li class="empty-state" role="presentation">
                <div class="empty-state-card" role="status" aria-live="polite">
                    <span class="empty-state-icon" aria-hidden="true">
                        <i class="fas fa-search"></i>
                    </span>
                    <span class="empty-state-title">${msg("No results found")}</span>
                    <span class="empty-state-description">${emptyDescription}</span>
                </div>
            </li>`;
        }

        // Group by section
        const sections = new Map<string, CommandPaletteAction[]>();
        const noSection: CommandPaletteAction[] = [];

        for (const action of items) {
            if (action.section) {
                const group = sections.get(action.section) ?? [];
                group.push(action);
                sections.set(action.section, group);
            } else {
                noSection.push(action);
            }
        }

        const result: unknown[] = [];
        let globalIndex = 0;

        const renderItem = (action: CommandPaletteAction, index: number) => {
            const isSelected = index === this._selectedIndex;
            const currentIndex = index;
            return html`<li
                id=${this.#actionOptionId(index)}
                class=${classMap({ "action": true, "is-selected": isSelected })}
                role="option"
                aria-selected=${isSelected ? "true" : "false"}
                @click=${() => {
                    action.handler();
                    this._open = false;
                }}
                @mouseenter=${() => {
                    this._selectedIndex = currentIndex;
                }}
            >
                ${action.icon
                    ? html`<span class="action-icon">${unsafeHTML(action.icon)}</span>`
                    : nothing}
                <span class="action-title">${action.title}</span>
            </li>`;
        };

        for (const action of noSection) {
            result.push(renderItem(action, globalIndex++));
        }

        for (const [section, sectionActions] of sections) {
            result.push(html`<li class="section-label" role="presentation">${section}</li>`);
            for (const action of sectionActions) {
                result.push(renderItem(action, globalIndex++));
            }
        }

        return result;
    }

    protected override render() {
        const activeDescendantId =
            this.filteredActions[this._selectedIndex] !== undefined
                ? this.#actionOptionId(this._selectedIndex)
                : undefined;

        return html`
            <dialog
                aria-label=${msg("Command palette")}
                @close=${() => {
                    this._open = false;
                }}
                @click=${this.#handleDialogClick}
                @keydown=${this.#handleKeydown}
            >
                <div class="search-wrapper">
                    <svg
                        class="search-icon"
                        viewBox="0 0 16 16"
                        fill="none"
                        width="16"
                        height="16"
                        aria-hidden="true"
                    >
                        <circle
                            cx="6.5"
                            cy="6.5"
                            r="4.5"
                            stroke="currentColor"
                            stroke-width="1.5"
                        />
                        <line
                            x1="10.5"
                            y1="10.5"
                            x2="14"
                            y2="14"
                            stroke="currentColor"
                            stroke-width="1.5"
                            stroke-linecap="round"
                        />
                    </svg>
                    <input
                        type="search"
                        .value=${this._query}
                        @input=${this.#handleInput}
                        placeholder=${msg("Search admin pages...")}
                        aria-label=${msg("Search admin pages")}
                        role="combobox"
                        aria-controls="ak-admin-command-palette-results"
                        aria-expanded=${this._open ? "true" : "false"}
                        aria-activedescendant=${ifDefined(activeDescendantId)}
                        aria-autocomplete="list"
                        autocomplete="off"
                        spellcheck="false"
                    />
                </div>
                <ul
                    id="ak-admin-command-palette-results"
                    class="list"
                    role="listbox"
                    aria-label=${msg("Command palette results")}
                >
                    ${this.#renderActions()}
                </ul>
                <div class="footer">
                    <span class="footer-trigger">
                        <kbd>${this.#openHotkeyLabel}</kbd>
                    </span>
                    <span class="footer-hints">
                        <span class="footer-item">
                            <kbd>↑</kbd><kbd>↓</kbd>
                            <span>${msg("Navigate")}</span>
                        </span>
                        <span class="footer-item">
                            <kbd>↵</kbd>
                            <span>${msg("Open")}</span>
                        </span>
                        <span class="footer-item">
                            <kbd>Esc</kbd>
                            <span>${msg("Close")}</span>
                        </span>
                    </span>
                </div>
            </dialog>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-command-palette": AkAdminCommandPalette;
    }
}
