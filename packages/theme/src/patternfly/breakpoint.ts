import { createPfGlobal, instance } from "../shared.js";

const usePfBreakpoint = createPfGlobal("breakpoint");

// Every single `ref` you see here is a color that Authentik has yet to define, which
// is why the fallback is provided.

usePfBreakpoint(instance, {
    "xs": "@breakpoint.xs",
    "sm": "@breakpoint.sm",
    "md": "@breakpoint.md",
    "lg": "@breakpoint.lg",
    "xl": "@breakpoint.xl",
    "2xl": "@breakpoint.2xl",
});

const usePfHeightBreakpoint = createPfGlobal("height-breakpoint");

usePfHeightBreakpoint(instance, {
    "sm": "@height-breakpoint.sm",
    "md": "@height-breakpoint.md",
    "lg": "@height-breakpoint.lg",
    "xl": "@height-breakpoint.xl",
    "2xl": "@height-breakpoint.2xl",
});
