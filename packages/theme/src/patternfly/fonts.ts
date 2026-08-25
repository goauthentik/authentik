import { createPfGlobal, instance } from "../shared.js";
import { bridge } from "./bridge.js";

createPfGlobal("FontFamily")(
    instance,
    bridge("@font-family")("sans-serif", "display", "monospace")
);

const usePfFontWeight = createPfGlobal("FontWeight");
usePfFontWeight(instance, bridge("@font-weight")("light", "normal", "semi-bold", "bold"));
usePfFontWeight(instance, {
    "overpass.semi-bold": "@font-weight.semi-bold",
    "overpass.bold": "@font-weight.bold",
});
