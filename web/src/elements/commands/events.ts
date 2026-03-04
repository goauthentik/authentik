import { CommandPaletteCommand } from "#elements/commands/shared";

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKRegisterCommandsEvent extends Event {
    public static readonly eventName = "ak-register-commands";

    public readonly commands: CommandPaletteCommand[];
    constructor(commands: CommandPaletteCommand[]) {
        super(AKRegisterCommandsEvent.eventName, { bubbles: true, composed: true });

        this.commands = commands;
    }
}

declare global {
    interface WindowEventMap {
        [AKRegisterCommandsEvent.eventName]: AKRegisterCommandsEvent;
    }
}
