import type { PaletteCommandDefinition } from "#elements/commands/shared";

/**
 * Event dispatched when the available commands in the command palette change.
 * This is used by the command palette to update the list of available commands.
 */
export class AKCommandChangeEvent<D = unknown> extends Event {
    public static readonly eventName = "ak-command-change";

    public readonly commands: readonly PaletteCommandDefinition<D>[];
    public readonly previousCommands: readonly PaletteCommandDefinition<D>[] | null;

    constructor(
        commands: PaletteCommandDefinition<D>[],
        previousCommands?: PaletteCommandDefinition<D>[] | null,
    ) {
        super(AKCommandChangeEvent.eventName, { bubbles: true, composed: true });

        this.commands = commands;
        this.previousCommands = previousCommands ?? null;
    }
}

declare global {
    interface WindowEventMap {
        [AKCommandChangeEvent.eventName]: AKCommandChangeEvent;
    }
}
