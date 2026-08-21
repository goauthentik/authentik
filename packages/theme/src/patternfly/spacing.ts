import { createPfGlobal, instance } from "../shared.js";

const usePfSpacer = createPfGlobal("spacer");

usePfSpacer(instance, {
    "xs": "@spacer.xs",
    "sm": "@spacer.sm",
    "md": "@spacer.md",
    "lg": "@spacer.lg",
    "xl": "@spacer.xl",
    "2xl": "@spacer.2xl",
    "3xl": "@spacer.3xl",
    "4xl": "@spacer.4xl",
    "form-element": "@spacer.form-element",
});
