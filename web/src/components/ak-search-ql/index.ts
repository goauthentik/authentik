import "#elements/buttons/Dropdown";

import { StripHTMLTrustPolicy } from "#common/purify";
import { rootInterface } from "#common/theme";

import { FormAssociated, FormAssociatedElement } from "#elements/forms/form-associated-element";
import { PaginatedResponse } from "#elements/table/Table";

import DjangoQL, { Introspections } from "@mrmarble/djangoql-completion";

import { msg } from "@lit/localize";
import { css, CSSResult, html, LitElement, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

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

/**
 * Given an array or length, return logical index of the element at the given delta.
 * This is effectively a modulo loop, allowing for positive and negative deltas.
 */
function torusIndex(lengthLike: number | ArrayLike<number>, delta: number): number {
    const length = typeof lengthLike === "number" ? lengthLike : lengthLike.length;

    if (delta < 0) {
        return (length + delta) % length;
    }

    return ((delta % length) + length) % length;
}

@customElement("ak-search-ql")
export class QLSearch extends FormAssociatedElement<string> implements FormAssociated {
    declare anchorRef: Ref<HTMLTextAreaElement>;
    declare anchor: HTMLTextAreaElement | null;

    public static styles: CSSResult[] = [
        PFBase,
        PFFormControl,
        PFSearchInput,
        css`
            ::-webkit-search-cancel-button {
                display: none;
            }

            .ql.pf-c-form-control {
                --input-height: 2.25em;

                height: var(--input-height);
                min-height: var(--input-height);
                max-height: calc(var(--input-height) * 6);
                resize: vertical;
            }

            .selected {
                background-color: var(--pf-c-search-input__menu-item--hover--BackgroundColor);
            }

            :host([theme="dark"]) {
                .pf-c-search-input__menu {
                    --pf-c-search-input__menu--BackgroundColor: var(--ak-dark-background-light-ish);
                    color: var(--ak-dark-foreground);
                }

                .pf-c-search-input__menu-item {
                    --pf-c-search-input__menu-item--Color: var(--ak-dark-foreground);
                }

                .pf-c-search-input__menu-item:hover {
                    --pf-c-search-input__menu-item--BackgroundColor: var(
                        --ak-dark-background-lighter
                    );
                }

                .pf-c-search-input__menu-list-item.selected {
                    --pf-c-search-input__menu-item--hover--BackgroundColor: var(
                        --ak-dark-background-light
                    );
                }

                .pf-c-search-input__text::before {
                    border: 0;
                }
            }

            .pf-c-search-input__menu {
                position: fixed;
                min-width: 0;
                overflow-y: auto;
                max-height: 50vh;
            }
        `,
    ];

    //#region Properties

    @property({ type: Boolean })
    public open = false;

    @property({ type: Number, attribute: false })
    public selectionIndex = -1;

    #value = "";

    @property({ type: String })
    public get value(): string {
        return this.#value;
    }

    public set value(value: unknown) {
        const parsed = typeof value === "string" ? value : "";

        this.setFormValue(parsed.trim(), parsed);
        this.#value = parsed;

        if (this.anchor) {
            this.anchor.value = this.#value;
        }
    }

    //#endregion

    //#region State

    #menuRef = createRef<HTMLDivElement>();

    #ql: QL | null = null;
    #ctx: OffscreenCanvasRenderingContext2D | null = null;
    #letterWidth = -1;
    #scrollContainer: HTMLElement | null = null;

    public set apiResponse(value: PaginatedResponse<unknown> | undefined) {
        if (!value?.autocomplete || !this.#ql) {
            return;
        }

        this.#ql.loadIntrospections(value.autocomplete as unknown as Introspections);
    }

    //#endregion

    //#region Lifecycle

    public override connectedCallback() {
        super.connectedCallback();

        this.internals.ariaAutoComplete = "list";
        this.internals.role = "combobox";
        this.internals.ariaHasPopup = "listbox";

        this.#scrollContainer =
            rootInterface<LitElement>().renderRoot.querySelector("#main-content");

        this.#scrollContainer?.addEventListener("scroll", this.#updateDropdownPosition, {
            passive: true,
        });

        this.tabIndex = 0;
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();

        this.#scrollContainer?.removeEventListener("scroll", this.#updateDropdownPosition);
    }

    public formStateRestoreCallback(state: string) {
        this.value = state;
    }

    public formResetCallback() {
        this.value = "";
    }

    public toJSON() {
        return this.value;
    }

    public override updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("open")) {
            this.internals.ariaExpanded = this.open ? "true" : "false";
        }

        if (changedProperties.has("selectionIndex")) {
            const id = `suggestion-${this.selectionIndex}`;

            this.setAttribute("aria-activedescendant", this.selectionIndex === -1 ? "" : id);

            this.renderRoot.querySelector(`#${id}`)?.scrollIntoView({
                behavior: "auto",
                block: "nearest",
            });
        }
    }

    public override firstUpdated() {
        const textarea = this.anchorRef.value;

        if (!textarea) return;

        this.#ql = new QL({
            completionEnabled: true,
            introspections: {
                current_model: "",
                models: {},
            },
            selector: textarea,
            autoResize: false,
        });

        const canvas = new OffscreenCanvas(300, 150);
        this.#ctx = canvas.getContext("2d");

        if (!this.#ctx) {
            console.error("authentik/ql: failed to get canvas context");
            return;
        }

        this.#ctx.font = window.getComputedStyle(textarea).font;

        // We need the width of a letter to measure x; we use a monospaced font but still
        // check the length for `m` as its the widest ASCII char
        const metrics = this.#ctx?.measureText("m");
        this.#letterWidth = Math.ceil(metrics?.width || 0) + 1;
    }

    //#endregion

    //#region Completions

    #refreshCompletions = () => {
        if (this.anchor) {
            this.value = this.anchor.value;
        }

        if (!this.#ql) {
            return;
        }

        this.#ql.generateSuggestions();

        if (this.#ql.suggestions.length < 1 || this.#ql.loading) {
            this.open = false;
            return;
        }

        this.open = true;

        this.requestUpdate();

        requestAnimationFrame(this.#updateDropdownPosition);
    };

    #updateDropdownPosition = () => {
        const anchor = this.anchorRef.value;
        const menu = this.#menuRef.value;

        if (!anchor || !menu) return;

        const bcr = this.getBoundingClientRect();
        const style = window.getComputedStyle(anchor);

        // Mostly static variables for padding, font line-height and how many
        const lineHeight = parseInt(style.lineHeight, 10);
        const paddingTop = parseInt(style.paddingTop, 10);
        const paddingLeft = parseInt(style.paddingLeft, 10);
        const paddingRight = parseInt(style.paddingRight, 10);

        const actualInnerWidth = bcr.width - paddingLeft - paddingRight;

        let relX = 0;
        let relY = 1;
        let letterIndex = 0;

        for (const word of anchor.value.split(" ")) {
            letterIndex += word.length;
            const newRelX = relX + word.length * this.#letterWidth;

            if (newRelX > actualInnerWidth) {
                relY += 1;

                if (letterIndex > anchor.selectionStart) {
                    relX =
                        this.#letterWidth * word.length -
                        (letterIndex - anchor.selectionStart) * this.#letterWidth;

                    break;
                }

                relX = word.length * this.#letterWidth;
            } else {
                relX = newRelX + 1;
            }
        }

        const x = bcr.x + paddingLeft + relX;
        const y = bcr.y + paddingTop + relY * lineHeight;

        Object.assign(menu.style, {
            left: `${x}px`,
            top: `${y}px`,
        } satisfies Partial<CSSStyleDeclaration>);
    };

    //#endregion

    //#region Event Listeners

    #keydownListener = (event: KeyboardEvent) => {
        this.#updateDropdownPosition();

        const suggestionsLength = this.#ql?.suggestions.length;

        if (event.key === "Enter" && !this.open && this.form) {
            const submitEvent = new SubmitEvent("submit", {
                submitter: this,
                bubbles: true,
                composed: true,
                cancelable: true,
            });

            this.form.dispatchEvent(submitEvent);

            return;
        }

        if (event.key === "ArrowDown") {
            event.preventDefault();

            if (this.open && suggestionsLength) {
                if (this.selectionIndex === -1) {
                    this.selectionIndex = 0;
                } else {
                    this.selectionIndex = torusIndex(suggestionsLength, this.selectionIndex + 1);
                }

                this.#refreshCompletions();

                return;
            }

            this.selectionIndex = 0;
            this.#refreshCompletions();

            return;
        }

        if (!this.open) return;

        switch (event.key) {
            case "ArrowUp":
                if (suggestionsLength) {
                    if (this.selectionIndex === -1) {
                        this.selectionIndex = suggestionsLength - 1;
                    } else {
                        this.selectionIndex = torusIndex(
                            suggestionsLength,
                            this.selectionIndex - 1,
                        );
                    }

                    this.#refreshCompletions();
                    event.preventDefault();
                }

                return;

            case "Tab":
                if (this.selectionIndex) {
                    this.#ql?.selectCompletion(this.selectionIndex);
                    event.preventDefault();
                }

                return;
            case "Enter":
                // Technically this is a textarea, due to automatic multi-line feature,
                // but other than that it should look and behave like a normal input.
                // So expected behavior when pressing Enter is to submit the form,
                // not to add a new line.
                if (this.selectionIndex !== -1) {
                    this.#ql?.selectCompletion(this.selectionIndex);
                    this.selectionIndex = 0;
                }

                event.preventDefault();

                return;
            case "Escape":
                this.open = false;
                return;
        }
    };

    #blurListener = ({ relatedTarget }: FocusEvent) => {
        if (relatedTarget instanceof Node && this.renderRoot.contains(relatedTarget)) {
            return;
        }

        this.open = false;
    };

    #focusListener = () => {
        this.selectionIndex = this.selectionIndex === -1 ? 0 : this.selectionIndex;

        this.#refreshCompletions();
    };

    //#endregion

    //#region Render

    protected renderMenu() {
        if (!this.open || !this.#ql) {
            return nothing;
        }

        return html`
            <div ${ref(this.#menuRef)} class="pf-c-search-input__menu">
                <ul
                    class="pf-c-search-input__menu-list"
                    role="listbox"
                    id="ql-suggestions"
                    aria-label=${msg("Query suggestions")}
                >
                    ${this.#ql.suggestions.map((suggestion, idx) => {
                        // Cast to string to sooth Lit Analyzer's primitive type rule.
                        const label = `${StripHTMLTrustPolicy.createHTML(suggestion.suggestionText)}`;

                        return html`<li
                            role="option"
                            id="suggestion-${idx}"
                            aria-selected=${this.selectionIndex === idx ? "true" : "false"}
                            class="pf-c-search-input__menu-list-item ${this.selectionIndex === idx
                                ? "selected"
                                : ""}"
                        >
                            <button
                                class="pf-c-search-input__menu-item"
                                type="button"
                                aria-label=${label}
                                @click=${() => {
                                    this.#ql?.selectCompletion(idx);
                                    this.#refreshCompletions();
                                }}
                            >
                                <span class="pf-c-search-input__menu-item-text pf-m-monospace">
                                    ${suggestion.text}</span
                                >
                            </button>
                        </li>`;
                    })}
                </ul>
            </div>
        `;
    }

    public override render(): TemplateResult {
        return html`<div class="pf-c-search-input">
            <div class="pf-c-search-input__bar">
                <span class="pf-c-search-input__text">
                    <textarea
                        ${ref(this.anchorRef)}
                        class="pf-c-form-control pf-m-monospace ql"
                        name="search"
                        autocomplete="off"
                        aria-controls="ql-suggestions"
                        ?required=${this.required}
                        placeholder=${msg("Search...")}
                        spellcheck="false"
                        @input=${this.#refreshCompletions}
                        @focus=${this.#focusListener}
                        @blur=${this.#blurListener}
                        @keydown=${this.#keydownListener}
                    >
${ifDefined(this.#value)}</textarea
                    >
                </span>
            </div>
            ${this.renderMenu()}
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-ql": QLSearch;
    }
}
