import { createPfGlobal, instance } from "../shared.js";
import { bridge } from "./bridge.js";

const usePfFontFamily = createPfGlobal("FontFamily");
usePfFontFamily(instance, {
    "sans-serif": "@font-family.sans-serif",
    "heading.sans-serif": "@font-family.display",
    "monospace": "@font-family.monospace",
});

const usePfFontWeight = createPfGlobal("FontWeight");
usePfFontWeight(instance, bridge("@font-weight")("light", "normal", "semi-bold", "bold"));
usePfFontWeight(instance, {
    "overpass.semi-bold": "@font-weight.semi-bold",
    "overpass.bold": "@font-weight.bold",
});
