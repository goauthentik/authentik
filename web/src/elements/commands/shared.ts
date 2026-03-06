import { SlottedTemplateResult } from "#elements/types";

export interface CommandPaletteCommand {
    label: SlottedTemplateResult;
    prefix?: SlottedTemplateResult;
    suffix?: SlottedTemplateResult;
    description?: SlottedTemplateResult;
    group?: string;
    action: () => unknown | Promise<unknown>;
}
