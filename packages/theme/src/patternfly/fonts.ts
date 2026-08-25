import { createPfGlobal, instance } from "../shared.js";

const usePfFontFamily = createPfGlobal("FontFamily");

usePfFontFamily(instance, {
    "sans-serif": "@font-family.sans-serif",
    "display": "@font-family.display",
    "monospace": "@font-family.monospace",
});

const usePfFontSize = createPfGlobal("FontSize");

usePfFontSize(instance, {
    "xs": "@font-size.xs",
    "sm": "@font-size.sm",
    "md": "@font-size.md",
    "lg": "@font-size.lg",
    "xl": "@font-size.xl",
    "2xl": "@font-size.2xl",
    "3xl": "@font-size.3xl",
    "4xl": "@font-size.4xl",
});

const usePfFontWeight = createPfGlobal("FontWeight");

usePfFontWeight(instance, {
    "light": "@font-weight.light",
    "normal": "@font-weight.normal",
    "semi-bold": "@font-weight.semi-bold",
    "overpass.semi-bold": "@font-weight.semi-bold",
    "bold": "@font-weight.bold",
    "overpass.bold": "@font-weight.bold",
});

const useLineHeight = createPfGlobal("LineHeight");

export const lineHeight = useLineHeight(instance, {
    sm: "1.3",
    md: "1.5",
});
