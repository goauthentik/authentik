import { createPfGlobal, instance } from "../shared.js";

const usePfBoxShadow = createPfGlobal("BoxShadow");

// One-to-one. authentik's `box-shadow.*` tokens are derived from these exact
// PatternFly values in `../authentik/shadow.ts`, so no fallbacks are needed
// and nothing here should ever resolve to a `ref`.
//
// Order follows PatternFly's own: each size, then its four edge variants.

usePfBoxShadow(instance, {
    "sm": "@box-shadow.sm",
    "sm-top": "@box-shadow.sm-top",
    "sm-right": "@box-shadow.sm-right",
    "sm-bottom": "@box-shadow.sm-bottom",
    "sm-left": "@box-shadow.sm-left",

    "md": "@box-shadow.md",
    "md-top": "@box-shadow.md-top",
    "md-right": "@box-shadow.md-right",
    "md-bottom": "@box-shadow.md-bottom",
    "md-left": "@box-shadow.md-left",

    "lg": "@box-shadow.lg",
    "lg-top": "@box-shadow.lg-top",
    "lg-right": "@box-shadow.lg-right",
    "lg-bottom": "@box-shadow.lg-bottom",
    "lg-left": "@box-shadow.lg-left",

    "xl": "@box-shadow.xl",
    "xl-top": "@box-shadow.xl-top",
    "xl-right": "@box-shadow.xl-right",
    "xl-bottom": "@box-shadow.xl-bottom",
    "xl-left": "@box-shadow.xl-left",

    "inset": "@box-shadow.inset",
});
