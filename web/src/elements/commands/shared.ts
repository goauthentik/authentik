export interface CommandPaletteCommand {
    label: string;
    description?: string;
    group?: string;
    action: () => void | Promise<void>;
}
