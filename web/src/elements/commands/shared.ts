export interface CommandPaletteCommand {
    label: string;
    prefix?: string;
    suffix?: string;
    description?: string;
    group?: string;
    action: () => unknown | Promise<unknown>;
}
