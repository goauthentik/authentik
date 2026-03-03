import "#elements/EmptyState";

import Styles from "./ak-command-palette.css";

import { torusIndex } from "#common/collections";
import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { AKModal } from "#elements/modals/ak-modal";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";
import { FocusTarget } from "#elements/utils/focus";

import { ConsoleLogger, Logger } from "#logger/browser";

import Fuse from "fuse.js";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface CommandPaletteCommand {
    label: string;
    description?: string;
    group?: string;
    action: () => void | Promise<void>;
}

const DEFAULT_COMMANDS: CommandPaletteCommand[] = [
    {
        label: "Go to dashboard",
        description: "Navigate to the dashboard",
        action: () => {
            window.location.href = "/dashboard";
        },
    },
    {
        label: "Open user settings",
        description: "Navigate to user settings",
        action: () => {
            window.location.href = "/settings";
        },
    },
];

@customElement("ak-command-palette-modal")
export class AKCommandPaletteModal extends AKModal {
    static openOnConnect = false;

    static styles = [...AKModal.styles, Styles];

    static open = asInvoker(AKCommandPaletteModal);

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();

    protected fuse = new Fuse<CommandPaletteCommand>([], {
        keys: [
            // ---
            { name: "label", weight: 3 },
            "description",
            "group",
        ],
        findAllMatches: true,
        includeScore: true,
        shouldSort: true,
        ignoreFieldNorm: true,
        useExtendedSearch: true,
        threshold: 0.3,
    });

    //#region Public Properties

    @property({ type: Number, attribute: false, useDefault: true })
    public selectionIndex = -1;

    @property({ type: Array, attribute: false, useDefault: true })
    public visibleCommands: CommandPaletteCommand[] = [];

    @property({ attribute: false, type: Array })
    public commands: CommandPaletteCommand[] = DEFAULT_COMMANDS;

    public override size = PFSize.Medium;

    public override focus = this.autofocusTarget.focus;

    //#region Lifecycle

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("focus", this.autofocusTarget.toEventListener());
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("commands")) {
            this.fuse.setCollection(this.commands);
            this.refreshVisibleCommands();
        }

        if (changedProperties.has("open") && this.open) {
            requestAnimationFrame(() => {
                this.autofocusTarget.focus();
            });
        }

        if (changedProperties.has("selectionIndex")) {
            const id = `suggestion-${this.selectionIndex}`;

            this.renderRoot.querySelector(`#${id}`)?.scrollIntoView({
                behavior: "auto",
                block: "nearest",
            });
        }
    }

    //#endregion

    public refreshVisibleCommands = () => {
        const value = this.autofocusTarget.target?.value.trim() || "";

        if (!value) {
            this.visibleCommands = this.commands;
            return;
        }

        this.visibleCommands = this.fuse.search(value).map((result) => result.item);
    };

    public submit() {
        if (!this.form) return;

        const submitEvent = new SubmitEvent("submit", {
            submitter: this,
            bubbles: true,
            composed: true,
            cancelable: true,
        });

        this.form.dispatchEvent(submitEvent);
    }

    #submitListener = (_event: SubmitEvent) => {
        const command = this.visibleCommands[this.selectionIndex];

        if (!command) return;

        this.open = false;
        command.action();
    };

    //#region Event Listeners

    #keydownListener = (event: KeyboardEvent) => {
        const visibleCommandsCount = this.visibleCommands.length;

        if (event.key === "Enter" && !this.open && this.form) {
            this.submit();

            return;
        }

        if (event.key === "ArrowDown") {
            event.preventDefault();

            if (this.open && visibleCommandsCount) {
                if (this.selectionIndex === -1) {
                    this.selectionIndex = 0;
                } else {
                    this.selectionIndex = torusIndex(visibleCommandsCount, this.selectionIndex + 1);
                }

                this.refreshVisibleCommands();

                return;
            }

            this.selectionIndex = 0;
            this.refreshVisibleCommands();

            return;
        }

        if (!this.open) return;

        switch (event.key) {
            case "ArrowUp":
                if (visibleCommandsCount) {
                    if (this.selectionIndex === -1) {
                        this.selectionIndex = visibleCommandsCount - 1;
                    } else {
                        this.selectionIndex = torusIndex(
                            visibleCommandsCount,
                            this.selectionIndex - 1,
                        );
                    }

                    this.refreshVisibleCommands();
                    event.preventDefault();
                }

                return;

            case "Enter":
                if (this.selectionIndex) {
                    this.submit();
                    event.preventDefault();
                }

                return;
        }
    };

    #focusListener = () => {
        this.selectionIndex = this.selectionIndex === -1 ? 0 : this.selectionIndex;

        this.refreshVisibleCommands();
    };

    //#region Rendering

    protected override renderCloseButton(): SlottedTemplateResult {
        return null;
    }

    protected renderCommands() {
        return html`<div class="pf-c-search-input__menu">
            <ul
                class="pf-c-search-input__menu-list"
                role="listbox"
                id="command-suggestions"
                aria-label=${msg("Query suggestions")}
            >
                ${this.visibleCommands.map((command, idx) => {
                    // Cast to string to sooth Lit Analyzer's primitive type rule.

                    return html`<li
                        role="option"
                        id="suggestion-${idx}"
                        aria-selected=${this.selectionIndex === idx ? "true" : "false"}
                        class="pf-c-search-input__menu-list-item ${this.selectionIndex === idx
                            ? "selected"
                            : ""}"
                    >
                        <button
                            class="pf-c-button pf-m-plain"
                            type="button"
                            aria-label=${command.label}
                            @click=${() => {
                                this.selectionIndex = idx;
                                this.refreshVisibleCommands();
                            }}
                        >
                            <span class="pf-c-search-input__menu-item-text pf-m-monospace">
                                ${command.label}</span
                            >
                        </button>
                    </li>`;
                })}
            </ul>
        </div>`;
    }

    protected override render() {
        return html`<form
            method="dialog"
            class="command-palette-form"
            @submit=${this.#submitListener}
        >
            <div
                class="pf-c-search-input"
                aria-expanded=${this.open ? "true" : "false"}
                aria-autocomplete="list"
                role="combobox"
                aria-label=${msg("Command palette")}
                aria-haspopup="listbox"
                aria-activedescendant=${this.selectionIndex === -1
                    ? ""
                    : `suggestion-${this.selectionIndex}`}
            >
                <div class="command-field">
                    <label class="sr-only" for="command-input">${msg("Type a command...")}</label>
                    <input
                        ${this.autofocusTarget.toRef()}
                        autofocus
                        id="command-input"
                        name="command"
                        aria-controls="command-suggestions"
                        type="search"
                        placeholder=${msg("Type a command...")}
                        class="pf-c-control command-input"
                        autocomplete="off"
                        autocapitalize="off"
                        spellcheck="false"
                        @input=${this.refreshVisibleCommands}
                        @focus=${this.#focusListener}
                        @keydown=${this.#keydownListener}
                    />
                </div>
            </div>
            ${this.renderCommands()}
        </form>`;
    }

    //#endregion
}

@customElement("ak-command-palette")
export class AKCommandPalette extends AKElement {
    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    protected logger: Logger;

    protected dialog: HTMLDialogElement;
    protected modal: AKCommandPaletteModal;

    constructor() {
        super();

        this.logger = ConsoleLogger.prefix(this.tagName.toLowerCase());

        this.dialog = this.ownerDocument.createElement("dialog");
        this.modal = this.ownerDocument.createElement("ak-command-palette-modal");

        this.dialog.appendChild(this.modal);
    }

    @listen("keydown", { passive: false, capture: true })
    protected keydownListener = (event: KeyboardEvent) => {
        if (event.key !== "k" || (!event.metaKey && !event.ctrlKey)) {
            return;
        }

        this.logger.info("Toggling command palette");

        event.preventDefault();

        this.modal.open = !this.modal.open;
    };

    protected override render() {
        return this.dialog;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette": AKCommandPalette;
        "ak-command-palette-modal": AKCommandPaletteModal;
    }
}
