/// <reference types="vite/client" />

import faIconsCSS from "#styles/global/vendor/patternfly-fa-icons.css?raw";
import pfIconsCSS from "#styles/global/vendor/patternfly-pf-icons.css?raw";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

/**
 * Read the icon names from the actual stylesheet, so we don't have to maintain our own lists.
 */
function iconNames(css: string, prefix: string): string[] {
    const pattern = new RegExp(`\\.(${prefix}[\\w-]+)::?before`, "g");
    const names = new Set(Array.from(css.matchAll(pattern), ([, name]) => name));

    return [...names].sort();
}

function renderGrid(names: string[], classesFor: (name: string) => string) {
    return html`<ul
        style="display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: 1rem; list-style: none; padding: 0;"
    >
        ${names.map(
            (name) =>
                html`<li
                    style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;"
                >
                    <i class=${classesFor(name)} style="font-size: 2rem;" aria-hidden="true"></i>
                    <code style="font-size: 0.75rem; overflow-wrap: anywhere;">${name}</code>
                </li>`,
        )}
    </ul>`;
}

const metadata: Meta = {
    title: "Elements/Icons",
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Icons

Show all of the icons in the vendored icon stylesheets we ship with our product.

There are blanks in the FontAwesome collection because we don't load the "brand"
icons, but they're defined in Patternfly's CSS.
`,
            },
        },
    },
};

export default metadata;

export const FontAwesome: StoryObj = {
    render: () => renderGrid(iconNames(faIconsCSS, "fa-"), (name) => `fas ${name}`),
};

export const PatternFlyIcons: StoryObj = {
    render: () => renderGrid(iconNames(pfIconsCSS, "pf-icon-"), (name) => name),
};
