import { AKCommandChangeEvent } from "#elements/commands/events";
import { SlottedTemplateResult } from "#elements/types";

export type PaletteCommandAction<D = unknown> = (data: D) => unknown | Promise<unknown>;

export interface PaletteCommandDefinition<D = unknown> {
    label: SlottedTemplateResult;
    keywords?: string[];
    prefix?: SlottedTemplateResult;
    suffix?: SlottedTemplateResult;
    description?: SlottedTemplateResult;
    group?: string;
    details?: D;
    action: PaletteCommandAction<D>;
}

export interface CommandPaletteStateInit<D = unknown> {
    commands?: PaletteCommandDefinition<D>[] | null;
    target?: EventTarget;
}

export class CommandPaletteState<D = unknown> {
    #commands: PaletteCommandDefinition<D>[] | null = null;
    #target: EventTarget;

    constructor({ commands = null, target = window }: CommandPaletteStateInit<D> = {}) {
        this.#commands = commands;
        this.#target = target ?? window;
    }

    public set(nextCommands: PaletteCommandDefinition<D>[] | null): void {
        const previousCommands = this.#commands;
        this.#commands = nextCommands;

        this.#target.dispatchEvent(new AKCommandChangeEvent(nextCommands ?? [], previousCommands));
    }

    public clear(): void {
        this.set(null);
    }
}
