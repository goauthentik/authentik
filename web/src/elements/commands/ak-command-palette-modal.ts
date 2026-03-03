import "#elements/EmptyState";

import { torusIndex } from "#common/collections";
import { PFSize } from "#common/enums";

import Styles from "#elements/commands/ak-command-palette-modal.css";
import { AKCommandChangeEvent } from "#elements/commands/events";
import { PaletteCommandDefinition } from "#elements/commands/shared";
import { listen } from "#elements/decorators/listen";
import { AKModal } from "#elements/modals/ak-modal";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";
import { FocusTarget } from "#elements/utils/focus";

import { AboutModal } from "#admin/AdminInterface/AboutModal";

import Fuse from "fuse.js";

import { msg, str } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { createRef, ref } from "lit-html/directives/ref.js";
import { customElement, property, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

function openDocsSearch(query: string) {
    const url = new URL("/search", import.meta.env.AK_DOCS_URL);
    url.searchParams.set("q", query);

    window.open(url, "_ak_docs", "noopener,noreferrer");
}

function createCommonCommands(): PaletteCommandDefinition<unknown>[] {
    return [
        {
            label: msg("Integrations"),
            prefix: msg("View", { id: "command-palette.prefix.view" }),
            action: () => window.open("https://integrations.goauthentik.io/", "_blank"),
            group: msg("Documentation"),
        },
        {
            label: msg("Release notes"),
            action: () => window.open(import.meta.env.AK_DOCS_RELEASE_NOTES_URL, "_blank"),
            prefix: msg("View", { id: "command-palette.prefix.view" }),
            suffix: msg(str`New in ${import.meta.env.AK_VERSION}`, {
                id: "command-palette.suffix.new-in",
            }),
            group: msg("authentik"),
        },
        {
            label: msg("About authentik"),
            action: AboutModal.open,
            prefix: msg("View", { id: "command-palette.prefix.view" }),
            group: msg("authentik"),
        },
    ];
}

@customElement("ak-command-palette-modal")
export class AKCommandPaletteModal extends AKModal {
    static openOnConnect = false;

    static styles = [...AKModal.styles, Styles];

    static open = asInvoker(AKCommandPaletteModal);

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();
    protected formRef = createRef<HTMLFormElement>();

    #scrollCommandFrameID = -1;
    #autoFocusFrameID = -1;

    // TODO: Fix form references.
    declare form: null;

    protected get value() {
        return this.autofocusTarget.target?.value.trim() || "";
    }

    protected fuse = new Fuse<PaletteCommandDefinition>([], {
        keys: [
            // ---
            { name: "label", weight: 3 },
            "description",
            "group",
            {
                name: "keywords",
                getFn: (command) => command.keywords?.join(" ") || "",
                weight: 2,
            },
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

    public get selectedCommand(): PaletteCommandDefinition | null {
        if (this.selectionIndex === -1) {
            return null;
        }

        return this.filteredCommands[this.selectionIndex] || null;
    }

    @property({ type: Number, attribute: false, useDefault: true })
    public maxCount = 20;

    @property({ type: Array, attribute: false, useDefault: true })
    public filteredCommands: readonly PaletteCommandDefinition<unknown>[] = [];

    /**
     * A map of the currently filtered commands to their index in the flattened commands array,
     * used to normalize the selection index while rendering groups.
     */
    #filteredCommandsIndex = new Map<PaletteCommandDefinition<unknown>, number>();
    /**
     * A flattened array of all commands in the command palette, used for filtering and selection.
     */
    #flattenedCommands: PaletteCommandDefinition<unknown>[] = [];

    @state()
    public commands = new Set<readonly PaletteCommandDefinition<unknown>[]>();

    public override size = PFSize.Medium;

    public override focus = this.autofocusTarget.focus;

    //#region Public Methods

    public setCommands = (
        commands?: readonly PaletteCommandDefinition<unknown>[] | null,
        previousCommands?: readonly PaletteCommandDefinition<unknown>[] | null,
    ) => {
        if (previousCommands) {
            this.commands.delete(previousCommands);
        }

        if (commands) {
            this.commands.add(commands);
            this.#flattenedCommands = Array.from(this.commands).reverse().flat();
        }

        const { target } = this.autofocusTarget;

        if (target) {
            target.value = "";
        }

        if (this.open && (commands || previousCommands)) {
            this.requestUpdate("commands");
        }
    };

    public scrollCommandIntoView = () => {
        const id = `command-${this.selectionIndex}`;

        const element = this.renderRoot.querySelector(`#${id}`);

        if (!element) {
            return;
        }

        const legend = element.closest("fieldset")?.querySelector("legend");

        legend?.scrollIntoView({
            behavior: "auto",
            block: "nearest",
        });

        element.scrollIntoView({
            behavior: "auto",
            block: "nearest",
        });
    };

    //#region Lifecycle

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("focus", this.autofocusTarget.toEventListener());

        requestAnimationFrame(() => {
            this.setCommands([
                {
                    label: msg("Documentation"),
                    action: () => openDocsSearch(this.value),
                    keywords: [msg("Docs"), msg("Readme"), msg("Help")],
                    prefix: msg("View", { id: "command-palette.prefix.view" }),
                    suffix: msg("New Tab", { id: "command-palette.suffix.view-docs" }),
                    group: msg("Documentation"),
                },
                ...createCommonCommands(),
            ]);
        });
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("commands")) {
            this.fuse.setCollection(this.#flattenedCommands);
            this.selectionIndex = 0;
            this.synchronizeFilteredCommands();
        }

        if (changedProperties.has("open") && this.open) {
            cancelAnimationFrame(this.#autoFocusFrameID);

            this.#autoFocusFrameID = requestAnimationFrame(() => {
                this.autofocusTarget.focus();
                this.autofocusTarget.target?.select();
            });
        }

        if (changedProperties.has("selectionIndex")) {
            cancelAnimationFrame(this.#scrollCommandFrameID);
            this.#scrollCommandFrameID = requestAnimationFrame(this.scrollCommandIntoView);
        }
    }

    //#endregion

    public synchronizeFilteredCommands = () => {
        cancelAnimationFrame(this.#scrollCommandFrameID);

        this.selectionIndex = 0;

        const { value } = this;

        if (value) {
            const filteredCommands = this.fuse
                .search(value, {
                    limit: this.maxCount,
                })
                .map((result) => result.item);

            filteredCommands.push({
                group: msg("Documentation"),
                label: msg(str`Search the docs for "${value}"`),
                prefix: msg("Open", { id: "command-palette.prefix.open" }),
                suffix: msg("New Tab", { id: "command-palette.suffix.view-docs" }),
                action: () => openDocsSearch(value),
            });

            this.filteredCommands = filteredCommands;
        } else {
            this.filteredCommands = this.#flattenedCommands.slice(0, this.maxCount);
        }

        this.#filteredCommandsIndex = new Map(
            this.filteredCommands.map((command, index) => [command, index]),
        );

        this.#scrollCommandFrameID = requestAnimationFrame(this.scrollCommandIntoView);
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
        command.action(command.details || null);
    };

    #commandClickListener = (event: MouseEvent) => {
        const target = event.currentTarget as HTMLElement;
        const index = parseInt(target.dataset.index!, 10);

        if (isNaN(index)) return;

        this.selectionIndex = index;
    };

    //#region Event Listeners

    @listen(AKCommandChangeEvent, {
        target: this,
    })
    protected commandChangeListener = (event: AKCommandChangeEvent) => {
        this.setCommands(event.commands, event.previousCommands);
    };

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

    protected renderCommands() {
        const { selectionIndex, value, filteredCommands } = this;

        return guard([filteredCommands, selectionIndex, value], () => {
            const grouped = Object.groupBy(filteredCommands, (command) => command.group || "");

            return html`<div
                part="results"
                role="listbox"
                id="command-suggestions"
                aria-label=${msg("Query suggestions")}
            >
                ${repeat(
                    Object.entries(grouped),
                    (_, groupIdx) => `group-${groupIdx}`,
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
                                role="presentation"
                            >
                                ${repeat(
                                    commands!,
                                    (_, commandIdx) => `group-${groupIdx}-command-${commandIdx}`,
                                    (command) => {
                                        const absoluteIdx =
                                            this.#filteredCommandsIndex.get(command) ?? -1;
                                        const { label, prefix, suffix, description } = command;

                                        const selected = selectionIndex === absoluteIdx;
                                        return html`<li
                                            role="presentation"
                                            id="command-${absoluteIdx}"
                                            aria-selected=${selected ? "true" : "false"}
                                            class="command-item ${selected ? "selected" : ""}"
                                            part="command-item"
                                        >
                                            <button
                                                part="command-button"
                                                type="submit"
                                                formmethod="dialog"
                                                data-index=${absoluteIdx}
                                                @click=${this.#commandClickListener}
                                                aria-labelledby="command-${absoluteIdx}-label"
                                                aria-describedby="command-${absoluteIdx}-description"
                                            >
                                                ${prefix
                                                    ? html`<div
                                                          part="command-item-prefix"
                                                          id="command-${absoluteIdx}-prefix"
                                                      >
                                                          ${prefix}
                                                      </div>`
                                                    : null}
                                                <div
                                                    part="command-item-label"
                                                    id="command-${absoluteIdx}-label"
                                                >
                                                    ${label}
                                                </div>
                                                ${suffix
                                                    ? html`<div
                                                          part="command-item-suffix"
                                                          id="command-${absoluteIdx}-suffix"
                                                      >
                                                          ${suffix}
                                                      </div>`
                                                    : null}
                                                <div
                                                    part="command-item-description"
                                                    id="command-${absoluteIdx}-description"
                                                >
                                                    ${description || ""}
                                                </div>
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
                        part="input-label"
                        for="command-input"
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
                        placeholder=${msg("What are you looking for?", {
                            id: "command-palette-placeholder-extended",
                            desc: "Placeholder for the command palette input",
                        })}
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
