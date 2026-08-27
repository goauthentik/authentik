import { createPfGlobal, instance, ref } from "../shared.js";

const usePfBackgroundColor = createPfGlobal("BackgroundColor");

// Every single `ref` you see here is a color that Authentik has yet to define, which
// is why the fallback is provided.

usePfBackgroundColor(instance, {
    "100": "@color.surface",
    "150": "@color.surface.subtle",
    "200": "@color.surface.canvas",
    "light-100": "@color.surface",
    "light-200": "@color.surface.subtle",
    "light-300": "@color.surface.canvas",
    "dark-100": "@color.decor",
    "dark-200": "@color.decor.subtle",
    "dark-300": "@color.decor.canvas",
    "dark-400": ref("color.dark-400", "#4f5255"),
    "dark-transparent-100": ref("color.dark-transparent-100", "rgba(3, 3, 3, 0.62)"),
    "dark-transparent-200": ref("color.dark-transparent-200", "rgba(3, 3, 3, 0.32)"),
});
