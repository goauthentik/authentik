import {
    ColorEntry,
    ColorGroupProp,
    Shade,
} from "@goauthentik/docusaurus-theme/components/infima/shared.ts";

const shades: Shade[] = [
    ["Darkest", "-darkest"],
    ["Darker", "-darker"],
    ["Dark", "-dark"],
    ["Default", ""],
    ["Light", "-light"],
    ["Lighter", "-lighter"],
    ["Lightest", "-lightest"],
];

export const InfimaColorsMap: ReadonlyMap<string, ColorGroupProp> = new Map([
    [
        "primary",
        {
            label: "Primary",
            cssVar: "color-primary",
            shades,
        },
    ],
    [
        "secondary",
        {
            label: "Secondary",
            cssVar: "color-secondary",
            shades,
        },
    ],
    [
        "success",
        {
            label: "Success",
            cssVar: "color-success",
            shades,
        },
    ],
    [
        "info",
        {
            label: "Info",
            cssVar: "color-info",
            shades,
        },
    ],
    [
        "warning",
        {
            label: "Warning",
            cssVar: "color-warning",
            shades,
        },
    ],
    [
        "danger",
        {
            label: "Danger",
            cssVar: "color-danger",
            shades,
        },
    ],
]);

export const UtilityColorEntries: readonly ColorEntry[] = [
    ["Background Color", "background-color"],
    ["Background Surface", "background-surface-color"],
    ["Font Color Base", "font-color-base"],
    ["Font Color Secondary", "font-color-secondary"],
    ["Content Color", "color-content"],
    ["Content Color Inverse", "color-content-inverse"],
    ["Content Color Secondary", "color-content-secondary"],
    ["Heading Color", "heading-color"],
    ["Link Color", "link-color"],
    ["Menu Color", "menu-color"],
    ["Menu Color Active", "menu-color-active"],
    ["Navbar Background", "navbar-background-color"],
    ["Footer Background", "footer-background-color"],
    ["Card Background", "card-background-color"],
    ["Code Background", "code-background"],
    ["Toc Border", "toc-border-color"],
    ["Table Stripe", "table-stripe-background"],
    ["Hover Overlay", "hover-overlay"],
];

export const DispositionInfoColorEntries: readonly ColorEntry[] = [
    ["Contrast Background", "color-info-contrast-background"],
    ["Dark", "color-info-dark"],
    ["Darker", "color-info-darker"],
    ["Darkest", "color-info-darkest"],
    ["Light", "color-info-light"],
    ["Lighter", "color-info-lighter"],
    ["Lightest", "color-info-lightest"],
];

export const DispositionSuccessColorEntries: readonly ColorEntry[] = [
    ["Contrast Background", "color-success-contrast-background"],
    ["Dark", "color-success-dark"],
    ["Darker", "color-success-darker"],
    ["Darkest", "color-success-darkest"],
    ["Light", "color-success-light"],
    ["Lighter", "color-success-lighter"],
    ["Lightest", "color-success-lightest"],
];
export const DispositionWarningColorEntries: readonly ColorEntry[] = [
    ["Contrast Background", "color-warning-contrast-background"],
    ["Dark", "color-warning-dark"],
    ["Darker", "color-warning-darker"],
    ["Darkest", "color-warning-darkest"],
    ["Light", "color-warning-light"],
    ["Lighter", "color-warning-lighter"],
    ["Lightest", "color-warning-lightest"],
];

export const DispositionDangerColorEntries: readonly ColorEntry[] = [
    ["Contrast Background", "color-danger-contrast-background"],
    ["Dark", "color-danger-dark"],
    ["Darker", "color-danger-darker"],
    ["Darkest", "color-danger-darkest"],
    ["Light", "color-danger-light"],
    ["Lighter", "color-danger-lighter"],
    ["Lightest", "color-danger-lightest"],
];
