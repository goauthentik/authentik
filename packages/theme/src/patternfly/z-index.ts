import { createPfGlobal, instance } from "../shared.js";

const usePfZIndex = createPfGlobal("ZIndex");

usePfZIndex(instance, {
    "xs": "@z-index.xs",
    "sm": "@z-index.sm",
    "md": "@z-index.md",
    "lg": "@z-index.lg",
    "xl": "@z-index.xl",
    "2xl": "@z-index.2xl",
});
