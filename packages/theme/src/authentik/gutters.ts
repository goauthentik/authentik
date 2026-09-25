import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useGutters = createUseVariable("gutter");

export const gutter = useGutters(instance, {
    default: "1rem",
    md: "1.5rem",
});
