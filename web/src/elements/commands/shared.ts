import { AKCommandChangeEvent } from "#elements/commands/events";
import { AKModal } from "#elements/modals/ak-modal";
import { SlottedTemplateResult } from "#elements/types";

import { AboutModal } from "#admin/AdminInterface/AboutModal";

import { msg, str } from "@lit/localize";

export const PaletteCommandNamespace = {
    Action: "action",
    Navigation: "navigation",
} as const;

export type PaletteCommandNamespace =
    (typeof PaletteCommandNamespace)[keyof typeof PaletteCommandNamespace];

/**
 * A symbol used to namespace commands in the command palette.
 * This is used to separate different types of commands, such as actions, navigation, etc.
 */
export const CommandNamespaceSymbol = {
    [PaletteCommandNamespace.Action]: ">",
    [PaletteCommandNamespace.Navigation]: "#",
} satisfies Record<PaletteCommandNamespace, string>;

/**
 * Given a user input, attempt to resolve it to a command namespace.
 * This is used to determine which commands to show in the command palette based on the user's input.
 */
export function resolveCommandNamespace(
    value: string,
): [query: string, namespace?: PaletteCommandNamespace] {
    for (const [namespace, symbol] of Object.entries(CommandNamespaceSymbol)) {
        const index = value.indexOf(symbol);

        if (index === -1) {
            continue;
        }

        return [value.slice(index + symbol.length), namespace as PaletteCommandNamespace];
    }

    return [value];
}

/**
 * Common human-readable prefixes for commands in the command palette.
 */
export const CommandPrefix = {
    JumpTo: () => msg("Jump to", { id: "command-palette.prefix.jump-to" }),
    SearchFor: () => msg("Search for", { id: "command-palette.prefix.search-for" }),
    Open: () => msg("Open", { id: "command-palette.prefix.open" }),
    View: () => msg("View", { id: "command-palette.prefix.view" }),
} as const;

export function formatNamespacePrefix(namespace: PaletteCommandNamespace): string | null {
    switch (namespace) {
        case PaletteCommandNamespace.Navigation:
            return CommandPrefix.JumpTo();
    }

    return null;
}

/**
 * Common human-readable suffixes for commands in the command palette.
 */
export const CommandSuffix = {
    NewTab: () => msg("New Tab", { id: "command-palette.suffix.new-tab" }),
} as const;

export type PaletteCommandAction<D = unknown> = (
    this: AKModal,
    data: D,
) => unknown | Promise<unknown>;

export interface PaletteCommandDefinitionInit<D = unknown> {
    namespace?: PaletteCommandNamespace;
    label: string;
    keywords?: string[];
    prefix?: string;
    suffix?: string;
    description?: SlottedTemplateResult;
    group?: string;
    details?: D;
    action: PaletteCommandAction<D>;
}

export interface PaletteCommandDefinition<D = unknown> extends PaletteCommandDefinitionInit<D> {
    namespace: PaletteCommandNamespace;
}

export interface CommandPaletteStateInit<D = unknown> {
    commands?: PaletteCommandDefinition<D>[] | null;
    target?: EventTarget;
}

export class CommandPaletteState<D = unknown> {
    #commands: PaletteCommandDefinition<D>[] | null = null;
    #target: EventTarget;

    declare parentElement: HTMLDialogElement | null;

    constructor({ commands = null, target = window }: CommandPaletteStateInit<D> = {}) {
        this.#commands = commands;
        this.#target = target ?? window;
    }

    public set(nextCommandsInit: PaletteCommandDefinitionInit<D>[] | null): void {
        const previousCommands = this.#commands;
        const nextCommands: PaletteCommandDefinition<D>[] = (nextCommandsInit ?? []).map(
            (command) => ({
                namespace: command.namespace ?? PaletteCommandNamespace.Action,
                ...command,
            }),
        );

        this.#commands = nextCommands;

        this.#target.dispatchEvent(new AKCommandChangeEvent(nextCommands, previousCommands));
    }

    public clear(): void {
        this.set(null);
    }
}

export function createCommonCommands(): PaletteCommandDefinitionInit<unknown>[] {
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
