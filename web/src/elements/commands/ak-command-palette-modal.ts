import "#elements/EmptyState";

import { torusIndex } from "#common/collections";
import { PFSize } from "#common/enums";

import Styles from "#elements/commands/ak-command-palette-modal.css";
import { AKRegisterCommandsEvent } from "#elements/commands/events";
import { CommandPaletteCommand } from "#elements/commands/shared";
import { listen } from "#elements/decorators/listen";
import { AKModal } from "#elements/modals/ak-modal";
import { asInvoker } from "#elements/modals/utils";
import { navigate } from "#elements/router/RouterOutlet";
import { SlottedTemplateResult } from "#elements/types";
import { FocusTarget } from "#elements/utils/focus";

import { AboutModal } from "#admin/AdminInterface/AboutModal";

import Fuse from "fuse.js";

import { msg, str } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { createRef, ref } from "lit-html/directives/ref.js";
import { customElement, property } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

@customElement("ak-command-palette-modal")
export class AKCommandPaletteModal extends AKModal {
    static openOnConnect = false;

    static styles = [...AKModal.styles, Styles];

    static open = asInvoker(AKCommandPaletteModal);

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();
    protected formRef = createRef<HTMLFormElement>();

    // TODO: Fix form references.
    declare form: null;

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

    @property({ type: Number, attribute: false, useDefault: true })
    public maxCount = 20;

    @property({ type: Array, attribute: false, useDefault: true })
    public filteredCommands: readonly CommandPaletteCommand[] = [];

    @property({ attribute: false, type: Array })
    public commands: CommandPaletteCommand[] = [
        {
            label: msg("Create a new application..."),
            action: () => navigate("/core/applications", { createWizard: true }),
            suffix: msg("Jump to", { id: "command-palette.prefix.jump-to" }),
            group: msg("Applications"),
        },
        {
            label: msg("Check the logs"),
            action: () => navigate("/events/log"),
            group: msg("Events"),
        },
        {
            label: msg("Manage users"),
            action: () => navigate("/identity/users"),
            group: msg("Users"),
        },
        {
            label: msg("Explore integrations"),
            action: () => window.open("https://integrations.goauthentik.io/", "_blank"),
            group: msg("authentik"),
        },
        {
            label: msg("Check the release notes"),
            action: () => window.open(import.meta.env.AK_DOCS_RELEASE_NOTES_URL, "_blank"),

            suffix: msg(str`New in ${import.meta.env.AK_VERSION}`, {
                id: "command-palette.suffix.new-in",
            }),
            group: msg("authentik"),
        },
        {
            label: msg("View documentation"),
            action: () => this.#openDocs(),
            suffix: msg("New Tab", { id: "command-palette.suffix.view-docs" }),
            group: msg("authentik"),
        },
        {
            label: msg("About authentik"),
            action: AboutModal.open,
            group: msg("authentik"),
        },
    ];

    public override size = PFSize.Medium;

    public override focus = this.autofocusTarget.focus;

    //#region Public Methods

    public addCommands = (commands: CommandPaletteCommand[]) => {
        this.commands = [...this.commands, ...commands];
    };

    public scrollCommandIntoView = (commandIndex = this.selectionIndex) => {
        const id = `command-${commandIndex}`;

        const element = this.renderRoot.querySelector(`#${id}`);

        element?.scrollIntoView({
            behavior: "auto",
            block: "nearest",
        });
    };

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
            this.scrollCommandIntoView();
        }
    }

    //#endregion

    #scrollCommandFrameID = -1;

    public synchronizeFilteredCommands = () => {
        cancelAnimationFrame(this.#scrollCommandFrameID);

        const { value } = this;

        if (!value) {
            this.filteredCommands = this.commands.slice(0, this.maxCount);
            return;
        }

        const filteredCommands = this.fuse
            .search(value, {
                limit: this.maxCount,
            })
            .map((result) => result.item);

        filteredCommands.push({
            label: msg(str`Search the docs for "${value}"`),
            suffix: msg("New Tab", { id: "command-palette.suffix.search-docs" }),
            action: this.#openDocs,
        });

        this.filteredCommands = filteredCommands;
        this.selectionIndex = 0;

        this.#scrollCommandFrameID = requestAnimationFrame(() => this.scrollCommandIntoView());
    };

    public submit() {
        const form = this.formRef.value;

        if (!form) return;

        const submitEvent = new SubmitEvent("submit", {
            submitter: this,
            bubbles: true,
            composed: true,
            cancelable: true,
        });

        form.dispatchEvent(submitEvent);
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

    @listen(AKRegisterCommandsEvent, {
        target: window,
    })
    protected registerCommandsListener(event: AKRegisterCommandsEvent) {
        this.commands = [...this.commands, ...event.commands];
    }

    #keydownListener = (event: KeyboardEvent) => {
        const visibleCommandsCount = this.filteredCommands.length;

        if (!this.open) {
            return;
        }

        if (event.key === "Enter" && this.form) {
            this.submit();

            return;
        }

        if (!visibleCommandsCount) {
            return;
        }

        switch (event.key) {
            case "ArrowDown":
                event.preventDefault();

                this.selectionIndex = torusIndex(visibleCommandsCount, this.selectionIndex + 1);
                return;

            case "ArrowUp":
                event.preventDefault();
                this.selectionIndex = torusIndex(visibleCommandsCount, this.selectionIndex - 1);

                return;

            case "Enter":
                event.preventDefault();
                this.submit();

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
        const { selectionIndex, value, filteredCommands } = this;

        return guard([filteredCommands, selectionIndex, value], () => {
            const grouped = Object.groupBy(filteredCommands, (command) => command.group || "");
            let commandCount = 0;

            return html`<div part="results">
                ${repeat(
                    Object.entries(grouped),
                    ([groupLabel]) => groupLabel,
                    ([groupLabel, commands], groupIdx) => html`
                        <fieldset part="results-group">
                            <legend
                                class="pf-c-content ${!groupLabel
                                    ? "sr-only more-contrast-only"
                                    : ""}"
                            >
                                <h2>${groupLabel || msg("Ungrouped")}</h2>
                            </legend>

                            <ul
                                part="results-list"
                                data-group-index=${groupIdx}
                                role="listbox"
                                id="command-suggestions"
                                aria-label=${msg("Query suggestions")}
                            >
                                ${repeat(
                                    commands!,
                                    (command) => command,
                                    ({ label, prefix, suffix }) => {
                                        const relativeIdx = commandCount;
                                        commandCount++;

                                        const selected = selectionIndex === relativeIdx;
                                        return html`<li
                                            role="option"
                                            id="command-${relativeIdx}"
                                            aria-selected=${selected ? "true" : "false"}
                                            class="command-item ${selected ? "selected" : ""}"
                                            part="command-item"
                                        >
                                            <button
                                                class="pf-c-button"
                                                type="submit"
                                                formmethod="dialog"
                                                data-index=${relativeIdx}
                                                @click=${this.#commandClickListener}
                                            >
                                                ${prefix
                                                    ? html`<span part="command-item-prefix"
                                                          >${prefix}</span
                                                      >`
                                                    : null}
                                                <span part="command-item-label">${label}</span>
                                                ${suffix
                                                    ? html`<span part="command-item-suffix"
                                                          >${suffix}</span
                                                      >`
                                                    : null}
                                            </button>
                                        </li>`;
                                    },
                                )}
                            </ul>
                        </fieldset>
                    `,
                )}
            </div>`;
        });
    }

    protected override render() {
        const { value, filteredCommands } = this;

        return html`<form
            ${ref(this.formRef)}
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
                <div part="command-field">
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
            ${!value && !filteredCommands.length
                ? html`<ak-empty-state icon="pf-icon-module"
                      ><span>${msg("No commands")}</span>
                      <div slot="body">${msg("No commands are currently available.")}</div>
                  </ak-empty-state>`
                : null}
        </form>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette-modal": AKCommandPaletteModal;
    }
}
