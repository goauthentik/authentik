import "#elements/EmptyState";

import { torusIndex } from "#common/collections";
import { PFSize } from "#common/enums";

import Styles from "#elements/commands/ak-command-palette-modal.css";
import { AKRegisterCommandsEvent } from "#elements/commands/events";
import { CommandPaletteCommand } from "#elements/commands/shared";
import { listen } from "#elements/decorators/listen";
import { AKModal } from "#elements/modals/ak-modal";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";
import { FocusTarget } from "#elements/utils/focus";

import Fuse from "fuse.js";

import { msg, str } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { customElement, property } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFSearchInput from "@patternfly/patternfly/components/SearchInput/search-input.css";

const DEFAULT_COMMANDS: CommandPaletteCommand[] = [
    {
        label: "Go to dashboard",
        description: "Navigate to the dashboard",
        action: () => {
            window.location.href = "/dashboard";
        },
    },
    {
        label: "Create an application...",
        description: "Navigate to the dashboard",
        action: () => {
            window.location.href = "/dashboard";
        },
    },
    {
        label: "Create a provider...",
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

    static styles = [...AKModal.styles, PFSearchInput, Styles];

    static open = asInvoker(AKCommandPaletteModal);

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();

    protected get value() {
        return this.autofocusTarget.target?.value.trim() || "";
    }

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
    public selectionIndex = 1;

    @property({ type: Array, attribute: false, useDefault: true })
    public filteredCommands: CommandPaletteCommand[] = [];

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
            this.selectionIndex = 0;
            this.synchronizeFilteredCommands();
        }

        if (changedProperties.has("open") && this.open) {
            requestAnimationFrame(() => {
                this.autofocusTarget.focus();
                this.autofocusTarget.target?.select();
            });
        }

        if (changedProperties.has("selectionIndex")) {
            const id = `command-${this.selectionIndex}`;

            this.renderRoot.querySelector(`#${id}`)?.scrollIntoView({
                behavior: "auto",
                block: "nearest",
            });
        }
    }

    //#endregion

    public synchronizeFilteredCommands = () => {
        const { value } = this;

        if (!value) {
            this.filteredCommands = this.commands;
            return;
        }

        this.filteredCommands = this.fuse.search(value).map((result) => result.item);

        this.filteredCommands.push({
            label: msg(str`Search the docs for "${value}"`),
            action: this.#openDocs,
        });
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

    #submitListener = (event: SubmitEvent) => {
        let commandIndex: number;
        if (event.submitter instanceof HTMLElement && event.submitter.dataset.index) {
            commandIndex = parseInt(event.submitter.dataset.index, 10);
        } else {
            commandIndex = this.selectionIndex;
        }

        const command = this.filteredCommands[commandIndex];

        if (!command) return;

        this.open = false;
        command.action();
    };

    #commandClickListener = (event: MouseEvent) => {
        const target = event.currentTarget as HTMLElement;
        const index = parseInt(target.dataset.index!, 10);

        if (isNaN(index)) return;

        this.selectionIndex = index;
    };

    //#region Event Listeners

    @listen(AKRegisterCommandsEvent)
    protected registerCommandsListener(event: AKRegisterCommandsEvent) {
        this.commands = [...this.commands, ...event.commands];
    }

    #keydownListener = (event: KeyboardEvent) => {
        const visibleCommandsCount = this.filteredCommands.length;

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

                this.synchronizeFilteredCommands();

                return;
            }

            this.selectionIndex = 0;
            this.synchronizeFilteredCommands();

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

                    this.synchronizeFilteredCommands();
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

        this.synchronizeFilteredCommands();
    };

    //#region Rendering

    protected override renderCloseButton(): SlottedTemplateResult {
        return null;
    }

    #openDocs = (): void => {
        const url = new URL("/search", import.meta.env.AK_DOCS_URL);
        url.searchParams.set("q", this.value);

        window.open(url, "_ak_docs", "noopener,noreferrer");
    };

    protected renderCommands() {
        const { selectionIndex, value } = this;
        const commands = this.filteredCommands.slice(0, 10);

        return guard([commands, selectionIndex, value], () => {
            return html`<div class="input__menu">
                <ul
                    class="input__menu-list"
                    role="listbox"
                    id="command-suggestions"
                    aria-label=${msg("Query suggestions")}
                >
                    ${repeat(
                        commands,
                        (command) => command,
                        (command, idx) => {
                            const selected = selectionIndex === idx;
                            return html`<li
                                role="option"
                                id="command-${idx}"
                                aria-selected=${selected ? "true" : "false"}
                                class="command-item ${selected ? "selected" : ""}"
                            >
                                <button
                                    class="pf-c-button"
                                    type="submit"
                                    formmethod="dialog"
                                    aria-label=${command.label}
                                    data-index=${idx}
                                    @click=${this.#commandClickListener}
                                >
                                    <span class="command-item__label">${command.label}</span>
                                </button>
                            </li>`;
                        },
                    )}
                </ul>
            </div>`;
        });
    }

    protected override render() {
        return html`<form
            method="dialog"
            class="command-palette-form"
            @submit=${this.#submitListener}
        >
            <div
                class="input"
                aria-expanded=${this.open ? "true" : "false"}
                aria-autocomplete="list"
                role="combobox"
                aria-label=${msg("Command palette")}
                aria-haspopup="listbox"
                aria-activedescendant=${this.selectionIndex === -1
                    ? ""
                    : `command-${this.selectionIndex}`}
            >
                <div class="command-field">
                    <label
                        part="label"
                        for="locale-selector"
                        @click=${this.show}
                        aria-label=${msg("Type a command...", {
                            id: "command-palette-placeholder",
                            desc: "Label for the command palette input",
                        })}
                    >
                        <svg
                            class="icon"
                            role="img"
                            aria-hidden="true"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 32 32"
                        >
                            <path
                                d="m29 27.586-7.552-7.552a11.018 11.018 0 1 0-1.414 1.414L27.586 29ZM4 13a9 9 0 1 1 9 9 9.01 9.01 0 0 1-9-9"
                            />
                        </svg>
                    </label>

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
                        @input=${this.synchronizeFilteredCommands}
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette-modal": AKCommandPaletteModal;
    }
}
