import { createPfGlobal, instance } from "../shared.js";

createPfGlobal("gutter")(instance, {
    default: "@gutter",
    md: "@gutter.md",
});
