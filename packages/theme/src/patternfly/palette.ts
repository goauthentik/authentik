import { rawPalette } from "../authentik/palette.js";
import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

export const usePaletteDesignTokens = createUseVariable("pf-global.palette");

export const palette = usePaletteDesignTokens(
    instance,
    Object.keys(rawPalette).reduce(
        (acc, key) => ({ ...acc, [key]: `@palette.${key}` }),
        {} satisfies Record<string, string>,
    ),
);
