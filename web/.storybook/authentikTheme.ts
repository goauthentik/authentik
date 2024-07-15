import { create } from "@storybook/theming/create";

const isDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;

export default create({
    base: isDarkMode ? "dark" : "light",
    brandTitle: "authentik Storybook",
    brandUrl: "https://goauthentik.io",
    brandImage: "https://goauthentik.io/img/icon_left_brand_colour.svg",
    brandTarget: "_self",
});
