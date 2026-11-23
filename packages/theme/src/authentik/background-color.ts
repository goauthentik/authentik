import { instance } from "../shared.js";

import { createUseVariable } from "@styleframe/theme";

const useDesignTokens = createUseVariable("color");

useDesignTokens(instance, {
    "surface": "#ffffff",
    "surface.canvas": "#f0f0f0",
    "surface.interactive": "#f0f0f0",
    "surface.subtle": "#fafafa",
    "surface.nested": "f1f9ff",
    "decor": "#151515",
    "decor.subtle": "#3c3f42",
    "decor.canvas": "#212427",
});
