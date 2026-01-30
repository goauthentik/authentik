import {
    ColorGroup,
    UtilityColor,
} from "@goauthentik/docusaurus-theme/components/infima/shared.ts";

export const infimalColors: ColorGroup[] = [
    {
        name: "Primary",
        cssVar: "--ifm-color-primary",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
    {
        name: "Secondary",
        cssVar: "--ifm-color-secondary",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
    {
        name: "Success",
        cssVar: "--ifm-color-success",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
    {
        name: "Info",
        cssVar: "--ifm-color-info",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
    {
        name: "Warning",
        cssVar: "--ifm-color-warning",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
    {
        name: "Danger",
        cssVar: "--ifm-color-danger",
        shades: [
            { name: "Darkest", suffix: "-darkest" },
            { name: "Darker", suffix: "-darker" },
            { name: "Dark", suffix: "-dark" },
            { name: "Default", suffix: "" },
            { name: "Light", suffix: "-light" },
            { name: "Lighter", suffix: "-lighter" },
            { name: "Lightest", suffix: "-lightest" },
        ],
    },
];

export const utilityColorDefs: UtilityColor[] = [
    { name: "Background Color", cssVar: "--ifm-background-color" },
    { name: "Background Surface", cssVar: "--ifm-background-surface-color" },
    { name: "Font Color Base", cssVar: "--ifm-font-color-base" },
    { name: "Font Color Secondary", cssVar: "--ifm-font-color-secondary" },
    { name: "Heading Color", cssVar: "--ifm-heading-color" },
    { name: "Link Color", cssVar: "--ifm-link-color" },
    { name: "Menu Color", cssVar: "--ifm-menu-color" },
    { name: "Menu Color Active", cssVar: "--ifm-menu-color-active" },
    { name: "Navbar Background", cssVar: "--ifm-navbar-background-color" },
    { name: "Footer Background", cssVar: "--ifm-footer-background-color" },
    { name: "Card Background", cssVar: "--ifm-card-background-color" },
    { name: "Code Background", cssVar: "--ifm-code-background" },
    { name: "Toc Border", cssVar: "--ifm-toc-border-color" },
    { name: "Table Stripe", cssVar: "--ifm-table-stripe-background" },
    { name: "Hover Overlay", cssVar: "--ifm-hover-overlay" },
];
