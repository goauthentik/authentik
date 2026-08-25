import { rawPalette } from "../authentik/palette.js";
import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

createUseVariable("pf-global.palette")(
    instance,
    Object.keys(rawPalette).reduce(
        (acc, key) => ({ ...acc, [key]: `@palette.${key}` }),
        {} satisfies Record<string, string>
    )
);
