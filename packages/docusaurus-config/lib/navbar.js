/**
 * @file Docusaurus navbar configuration for the authentik website.
 *
 * @import { NavbarItem } from "@docusaurus/theme-common";
 */

import { DocusaurusURL, SocialURL } from "./routing.js";

/**
 * The navbar items for the authentik website.
 *
 * @type {NavbarItem[]}
 */
export const SocialNavbarItems = /** @type {const} */ ([
    {
        "href": SocialURL.GitHub,
        "data-icon": "github",
        "aria-label": "GitHub",
        "position": "right",
    },
    {
        "href": SocialURL.Discord,
        "data-icon": "discord",
        "aria-label": "Discord",
        "position": "right",
    },
]);

/**
 * The navbar items for the authentik website.
 *
 * @satisfies {NavbarItem[]}
 */
export const NavbarItemsTemplate = /** @type {const} */ ([
    {
        to: "{{WWW_URL}}/features",
        label: "Features",
        position: "left",
        target: "_self",
    },
    {
        to: "{{INTEGRATIONS_URL}}",
        label: "Integrations",
        target: "_self",
        position: "left",
    },
    {
        to: "{{DOCS_URL}}",

        label: "Documentation",
        position: "left",
        target: "_self",
    },
    {
        to: "{{WWW_URL}}/pricing/",
        label: "Pricing",
        position: "left",
        target: "_self",
    },
    {
        to: "{{WWW_URL}}/blog",
        label: "Blog",
        position: "left",
        target: "_self",
    },
    ...SocialNavbarItems,
]);

/**
 * @typedef {Object} NavbarItemOverrides
 *
 * @prop {string} WWW_URL The URL for the WWW environment.
 * @prop {string} DOCS_URL The URL for the documentation.
 * @prop {string} INTEGRATIONS_URL The URL for the integrations.
 */

const DEFAULT_NAVBAR_REPLACEMENTS = /** @type {const} */ ({
    DOCS_URL: DocusaurusURL.Docs,
    INTEGRATIONS_URL: DocusaurusURL.Integrations,
    WWW_URL: DocusaurusURL.WWW,
});

/**
 * Creates a navbar item array, replacing placeholders with the given replacements.
 *
 * @param {Partial<NavbarItemOverrides>} [overrides]
 * @returns {NavbarItem[]}
 */
export function createNavbarItems(overrides) {
    const replacements = {
        ...DEFAULT_NAVBAR_REPLACEMENTS,
        ...overrides,
    };

    return NavbarItemsTemplate.map((item) => {
        if (typeof item.to !== "string") return item;

        return {
            ...item,
            to: item.to.replace(
                /{{([^}]+)}}/g,
                /**
                 * @param {keyof NavbarItemOverrides}  key
                 */
                (_, key) => {
                    return replacements[key];
                },
            ),
        };
    });
}
