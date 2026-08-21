import { createPfGlobal, instance } from "../shared.js";

const usePfGutter = createPfGlobal("gutter");

usePfGutter(instance, {
    "": "@gutter.",
    "md": "@gutter.md",
});
