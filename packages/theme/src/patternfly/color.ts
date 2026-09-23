import { createPfGlobal, instance, ref, variable } from "../shared.js";

const usePfColor = createPfGlobal("Color");
const usePfBackgroundColor = createPfGlobal("BackgroundColor");
const usePfBorderColor = createPfGlobal("BorderColor");

// Every single `ref` you see here is a color that Authentik has yet to define, which
// is why the fallback is provided.

usePfColor(instance, {
    "100": "@color.ink",
    "200": "@color.ink.muted",
    "300": "@color.ink.subtle",
    "400": "@color.ink.subtle",
    "light-100": "@color.ink.pin-light",
    "light-200": "@color.ink.pin-light",
    "light-300": "@color.ink.pin-light",
    "dark-100": "@color.ink.pin-dark",
    "dark-200": "@color.ink.pin-dark.muted",
    "dark-300": "@color.ink.pin-dark.subtle",
});

usePfBackgroundColor(instance, {
    "100": "@color.surface",
    "150": "@color.surface.raised",
    "200": "@color.surface.muted",
    "light-100": "@color.surface.pin-light",
    "light-200": "@color.surface.pin-light.raised",
    "light-300": "@color.surface.pin-light.muted",
    "dark-100": "@color.surface.pin-dark",
    "dark-200": "@color.surface.pin-dark.raised",
    "dark-300": "@color.surface.pin-dark.muted",
    "dark-400": ref("color.dark-400", "#4f5255"),
    "dark-transparent-100": "@color.scrim",
    "dark-transparent-200": "@color.scrim.light",
});

usePfBorderColor(instance, {
    "100": "@color.border",
    "200": "@color.border.edge",
    "300": "@color.border.subtle",
    "400": "#aaabac",
});

const pfvar = (pfKey: string, akKey: string) => variable(`pf-global.${pfKey}`, `${akKey}`);

// prettier-ignore
{
    pfvar("primary-color.100",       "@color.primary");
    pfvar("primary-color.200",       "@color.primary.active");
    pfvar("primary-color.300",       "#0066cc");
    pfvar("primary-color.light-100", "@color.primary.pin-dark");
    pfvar("primary-color.dark.100", "@color.primary.pin-light");
    pfvar("active-color.100",        "@color.active");
    pfvar("active-color.200",        "@color.active.fill");
    pfvar("active-color.300",        "@color.active.hover");
    pfvar("active-color.400",        "@color.active.hint");
    pfvar("disabled-color.100",      "@color.disabled");
    pfvar("disabled-color.200",      "@color.disabled.fill");
    pfvar("disabled-color.300",      "@color.disabled.readonly");
    pfvar("default-color.100",       "#73c5c5");
    pfvar("default-color.200",       "#009596");
    pfvar("default-color.300",       "@color.neutral.deep");
    pfvar("success-color.100",       "@color.success");
    pfvar("success-color.200",       "@color.success.fill");
    pfvar("success-color.300",       "@color.success.deep");
    pfvar("info-color.100",          "@color.info");
    pfvar("info-color.100",          "@color.info.fill");
    pfvar("info-color.100",          "@color.info.deep");
    pfvar("warning-color.100",       "@color.warning");
    pfvar("warning-color.100",       "@color.warning.fill");
    pfvar("warning-color.100",       "@color.warning.deep");
    pfvar("danger-color.100",        "@color.danger");
    pfvar("danger-color.100",        "@color.danger.tint");
    pfvar("danger-color.100",        "@color.danger.deep");
}
