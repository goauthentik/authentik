import "#elements/EmptyState";

import { torusIndex } from "#common/collections";
import { PFSize } from "#common/enums";

import Styles from "#elements/commands/ak-command-palette-modal.css";
import { AKCommandChangeEvent } from "#elements/commands/events";
import {
    CommandNamespaceSymbol,
    CommandPrefix,
    CommandSuffix,
    formatNamespacePrefix,
    PaletteCommandDefinition,
    PaletteCommandDefinitionInit,
    PaletteCommandNamespace,
    resolveCommandNamespace,
} from "#elements/commands/shared";
import { listen } from "#elements/decorators/listen";
import { AKModal } from "#elements/modals/ak-modal";
import { TransclusionElement } from "#elements/modals/shared";
import { asInvoker } from "#elements/modals/utils";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { FocusTarget } from "#elements/utils/focus";

import { AboutModal } from "#admin/AdminInterface/AboutModal";

import Fuse, { Expression } from "fuse.js";

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

function createCommonCommands(): PaletteCommandDefinitionInit<unknown>[] {
    return [
        {
            label: msg("Integrations"),
            prefix: msg("View", { id: "command-palette.prefix.view" }),
            suffix: CommandSuffix.NewTab(),
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
            label: msg("About authentik", {
                id: "command-palette.about-authentik",
            }),
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
    protected formRef = createRef<HTMLFormElement & TransclusionElement>();

    public readonly actionNamespaceSymbol = CommandNamespaceSymbol[PaletteCommandNamespace.Action];
    public readonly navigationNamespaceSymbol =
        CommandNamespaceSymbol[PaletteCommandNamespace.Navigation];

    #scrollCommandFrameID = -1;
    #autoFocusFrameID = -1;

    public get value() {
        return this.autofocusTarget.target?.value.trim() || "";
    }

    public set value(nextValue: string) {
        if (!this.autofocusTarget.target) {
            this.logger.warn(
                "Attempted to set command palette value before autofocus target was available",
            );
            return;
        }

        this.autofocusTarget.target.value = nextValue;
        this.synchronizeFilteredCommands();
    }

    protected fuse = new Fuse<PaletteCommandDefinition>([], {
        keys: [
            { name: "namespace", weight: 2 },

            {
                name: "label",
                weight: 2,
                getFn: ({ prefix, label }) => {
                    if (prefix) {
                        return [`${prefix}:${label}`, label];
                    }

                    return label;
                },
            },
            "description",
            { name: "group", weight: 1 },

            { name: "prefix", weight: 0.7 },
            { name: "suffix", weight: 0.25 },
            {
                name: "keywords",
                getFn: ({ keywords }) => keywords?.join(" ") || "",
                weight: 2,
            },
        ],
        findAllMatches: true,
        includeScore: true,
        shouldSort: true,
        ignoreFieldNorm: true,
        useExtendedSearch: true,
        isCaseSensitive: false,
    });

    //#region Public Properties

    @property({ type: Number, attribute: false, useDefault: true })
    public selectionIndex = 0;

    public get selectedCommand(): PaletteCommandDefinition | null {
        if (this.selectionIndex === -1) {
            return null;
        }

        return this.filteredCommands[this.selectionIndex] || null;
    }

    @property({ type: Number, attribute: false, useDefault: true })
    public maxCount = 200;

    @property({ type: Array, attribute: false, useDefault: true })
    public filteredCommands: readonly PaletteCommandDefinition<unknown>[] = [];

    /**
     * A flattened array of all commands in the command palette, used for filtering and selection.
     */
    #flattenedCommands: PaletteCommandDefinition<unknown>[] = [];

    /**
     * Commands ordered by their grouped render order, so that selectionIndex
     * maps correctly to the visually displayed list.
     */
    #renderOrderedCommands: readonly PaletteCommandDefinition<unknown>[] = [];

    @state()
    public commands = new Set<readonly PaletteCommandDefinition<unknown>[]>();

    public override size = PFSize.Medium;

    public override focus = this.autofocusTarget.focus;

    //#region Public Methods

    public setCommands = (
        commands?: readonly PaletteCommandDefinition<unknown>[] | null,
        previousCommands?: readonly PaletteCommandDefinition<unknown>[] | null,
    ) => {
        const changed = commands || previousCommands;
        const { target } = this.autofocusTarget;

        if (previousCommands) {
            this.commands.delete(previousCommands);
        }

        if (commands && commands.length) {
            this.commands.add(commands);
            this.#flattenedCommands = Array.from(this.commands).reverse().flat();
        }

        if (target) {
            target.value = "";
        }

        if (changed) {
            this.fuse.setCollection(this.#flattenedCommands);
        }

        if (this.open && changed) {
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
            this.setCommands(
                [
                    {
                        label: msg("Documentation"),
                        action: () => openDocsSearch(this.value),
                        keywords: [msg("Docs"), msg("Readme"), msg("Help")],
                        prefix: CommandPrefix.View(),
                        suffix: CommandSuffix.NewTab(),
                        group: msg("Documentation"),
                    },
                    ...createCommonCommands(),
                ].map((command) => ({ namespace: PaletteCommandNamespace.Action, ...command })),
            );
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

            this.logger.debug("Command palette opened, focusing input");
            this.#autoFocusFrameID = requestAnimationFrame(() => {
                this.autofocusTarget.focus();

                if (!this.value.startsWith(this.actionNamespaceSymbol)) {
                    this.autofocusTarget.target?.select();
                }
            });
        }

        if (changedProperties.has("selectionIndex")) {
            cancelAnimationFrame(this.#scrollCommandFrameID);
            this.#scrollCommandFrameID = requestAnimationFrame(this.scrollCommandIntoView);
        }
    }

    //#endregion

    protected collectFilteredCommands(): PaletteCommandDefinition<unknown>[] {
        const { value } = this;

        if (!value) {
            return this.#flattenedCommands.slice(0, this.maxCount);
        }

        const [query, namespace] = resolveCommandNamespace(value);

        let pattern: string | Expression;

        if (namespace) {
            const $and: Expression[] = [
                {
                    namespace: `=${namespace}`,
                },
            ];

            if (query) {
                $and.push({
                    label: query,
                });
            }

            pattern = {
                $and,
            };
        } else {
            pattern = value;
        }

        this.logger.debug("Filtering commands with pattern:", pattern);

        const filteredCommands = this.fuse
            .search(pattern, {
                limit: this.maxCount,
            })
            .map((result) => result.item);

        if (!namespace) {
            filteredCommands.push({
                group: msg("Documentation"),
                namespace: PaletteCommandNamespace.Action,
                label: msg(str`Search the docs for "${value}"`),
                prefix: msg("Open", { id: "command-palette.prefix.open" }),
                suffix: msg("New Tab", { id: "command-palette.suffix.view-docs" }),
                action: () => openDocsSearch(value),
            });
        }

        this.logger.debug("Filtered commands:", filteredCommands);

        return filteredCommands;
    }

    public synchronizeFilteredCommands = () => {
        cancelAnimationFrame(this.#scrollCommandFrameID);

        this.selectionIndex = 0;

        const filteredCommands = this.collectFilteredCommands();

        // Build render-ordered list that matches the grouped display order.
        const grouped = Object.groupBy(filteredCommands, (command) => command.group || "");
        this.#renderOrderedCommands = Object.values(
            grouped,
        ).flat() as PaletteCommandDefinition<unknown>[];

        this.filteredCommands = filteredCommands;

        this.#scrollCommandFrameID = requestAnimationFrame(this.scrollCommandIntoView);
    };

    public dispatchSubmit(event?: Event) {
        const form = this.formRef.value;

        if (!form) return;

        const submitter = event?.currentTarget instanceof HTMLElement ? event.currentTarget : this;

        const submitEvent = new SubmitEvent("submit", {
            submitter,
            bubbles: true,
            composed: true,
            cancelable: true,
        });

        form.dispatchEvent(submitEvent);
    }

    #submitListener = (event: SubmitEvent) => {
        event.preventDefault();
        event.stopPropagation();

        let commandIndex: number;
        if (event.submitter instanceof HTMLElement && event.submitter.dataset.commandIndex) {
            commandIndex = parseInt(event.submitter.dataset.commandIndex, 10);
        } else {
            commandIndex = this.selectionIndex;
        }

        const command = this.#renderOrderedCommands[commandIndex];

        if (!command) {
            this.logger.warn("No command found for index:", commandIndex);
            return;
        }

        this.open = false;
        command.action(command.details || null);
    };

    #commandClickListener = (event: MouseEvent) => {
        const target = event.currentTarget as HTMLElement;
        const index = parseInt(target.dataset.commandIndex!, 10);

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

        if (!this.open) return;
        if (!visibleCommandsCount) return;
        if (event.shiftKey || event.altKey) return;

        switch (event.key) {
            case "ArrowDown":
                event.preventDefault();

                this.selectionIndex = torusIndex(visibleCommandsCount, this.selectionIndex + 1);
                this.logger.info("Selected command index:", this.selectionIndex);
                return;

            case "ArrowUp":
                event.preventDefault();
                this.selectionIndex = torusIndex(visibleCommandsCount, this.selectionIndex - 1);
                this.logger.info("Selected command index:", this.selectionIndex);

                return;

            case "Enter":
                event.preventDefault();
                this.dispatchSubmit(event);

                return;
        }
    };

    #focusListener = () => {
        this.selectionIndex = this.selectionIndex === -1 ? 0 : this.selectionIndex;

        this.synchronizeFilteredCommands();
    };

    legendClickListener = (event: MouseEvent) => {
        const target = event.currentTarget as HTMLElement;

        const label = target.dataset.label;

        if (!label) return;

        this.value = `${label}:`;
        this.autofocusTarget.focus();
    };

    //#region Rendering

    protected override renderCloseButton(): SlottedTemplateResult {
        return null;
    }

    protected renderCommands() {
        const { selectionIndex, value, filteredCommands } = this;

        return guard([filteredCommands, selectionIndex, value], () => {
            const grouped = Object.groupBy(filteredCommands, (command) => command.group || "");

            let globalIndex = 0;

            return html`<div
                part="results"
                role="listbox"
                id="command-suggestions"
                aria-label=${msg("Query suggestions")}
            >
                ${repeat(
                    Object.entries(grouped),
                    (_group, groupIdx) => `group-${groupIdx}`,
                    ([groupLabel, commands], groupIdx) => html`
                        <fieldset part="results-group">
                            <legend
                                class="${!groupLabel ? "sr-only more-contrast-only" : ""}"
                                data-label=${ifPresent(groupLabel)}
                                @click=${this.legendClickListener}
                            >
                                <h2 class="pf-c-title pf-m-md">
                                    ${groupLabel || msg("Ungrouped")}
                                </h2>
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
                                        const { label, suffix, description, prefix, namespace } =
                                            command;

                                        const formattedPrefix =
                                            prefix || formatNamespacePrefix(namespace);

                                        const currentIndex = globalIndex++;
                                        const selected = selectionIndex === currentIndex;

                                        // const formattedLabel = groupLabel
                                        //     ? `${groupLabel}: ${label}`
                                        //     : label;

                                        return html`<li
                                            role="presentation"
                                            id="command-${currentIndex}"
                                            aria-selected=${selected ? "true" : "false"}
                                            class="command-item ${selected ? "selected" : ""}"
                                            part="command-item"
                                        >
                                            <button
                                                part="command-button"
                                                type="submit"
                                                formmethod="dialog"
                                                data-group-index=${groupIdx}
                                                data-command-index=${currentIndex}
                                                @click=${this.#commandClickListener}
                                                aria-labelledby="command-${currentIndex}-label"
                                                aria-describedby="command-${currentIndex}-description"
                                            >
                                                ${formattedPrefix
                                                    ? html`<div
                                                          part="command-item-prefix"
                                                          id="command-${currentIndex}-prefix"
                                                      >
                                                          ${formattedPrefix}
                                                      </div>`
                                                    : null}
                                                <div
                                                    part="command-item-label"
                                                    id="command-${currentIndex}-label"
                                                >
                                                    ${label}
                                                </div>
                                                ${suffix
                                                    ? html`<div
                                                          part="command-item-suffix"
                                                          id="command-${currentIndex}-suffix"
                                                      >
                                                          ${suffix}
                                                      </div>`
                                                    : null}
                                                <div
                                                    part="command-item-description"
                                                    id="command-${currentIndex}-description"
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
            ${this.renderCommands()} ${this.renderPlaceholder()}
        </form>`;
    }

    protected renderPlaceholder() {
        const { filteredCommands, value } = this;

        if (filteredCommands.length) {
            return null;
        }

        if (value.startsWith(this.actionNamespaceSymbol)) {
            return html`<ak-empty-state part="empty-state" icon="pf-icon-module"
                ><span>${msg("No commands")}</span>
                <div slot="body">
                    ${msg("No matching commands.", {
                        id: "command-palette.no-matching-commands",
                    })}
                </div>
            </ak-empty-state>`;
        }

        return html`<ak-empty-state part="empty-state" icon="pf-icon-module"
            ><span>${msg("No commands")}</span>
            <div slot="body">
                ${msg("No commands are currently available.", {
                    id: "command-palette.no-commands",
                })}
            </div>
        </ak-empty-state>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette-modal": AKCommandPaletteModal;
    }
}
