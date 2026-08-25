import { createPfGlobal, instance } from "../shared.js";

const usePfBorderRadius = createPfGlobal("BorderRadius");

usePfBorderRadius(instance, {
    sm: "@radius.sm",
    lg: "@radius.pill",
});

const usePfBorderWidth = createPfGlobal("BorderWidth");

usePfBorderWidth(instance, {
    sm: "@border-width.sm",
    md: "@border-width.md",
    lg: "@border-width.lg",
});
