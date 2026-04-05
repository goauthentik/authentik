import "../AppIcon.js";

import { AppIcon } from "../AppIcon.js";

import { PFSize } from "#common/enums";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const sizeOptions = Array.from(Object.values(PFSize));

const metadata: Meta<AppIcon> = {
    title: "Elements / <ak-app-icon>",
    component: "ak-app-icon",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Application Icon

AppIcon displays an icon associated with an authentik application on the User Library page. It takes
an API "Application" object and a size, with a default size of "medium."

## Usage

Note that the variables passed in are how they are used in authentik. Any string and any FontAwesome
icon supported by the current theme can be referenced.

\`\`\`Typescript
import "#components/ak-app-icon";
\`\`\`

\`\`\`html
<ak-app-icon name=\${app.name} icon=\${app.metaIconUrl}></ak-ak-app-icon>
\`\`\`
`,
            },
        },
    },

    argTypes: {
        name: { control: "text" },
        icon: { control: "text" },
        size: { options: sizeOptions, control: "select" },
    },
};

export default metadata;

const container = (testItem: TemplateResult) => html`
    <style>
        li {
            display: block;
        }
        p {
            margin-top: 1em;
        }
    </style>
    ${testItem}
`;

export const DefaultStory: StoryObj = {
    args: {
        name: "Demo App",
    },
    render: ({ name, icon, size }) =>
        container(
            html`<ak-app-icon
                size=${size}
                name=${ifDefined(name)}
                icon=${ifDefined(icon)}
            ></ak-app-icon>`,
        ),
};

export const WithIcon: StoryObj = {
    args: {
        name: "Iconic App",
        icon: "fa://fa-yin-yang",
    },
    render: ({ name, icon, size }) =>
        container(
            html`<ak-app-icon
                size=${size}
                name=${ifDefined(name)}
                icon=${ifDefined(icon || undefined)}
            ></ak-app-icon>`,
        ),
};

export const AllDataUndefined: StoryObj = {
    args: {},
    render: ({ name, icon, size }) =>
        container(
            html`<ak-app-icon
                size=${size}
                name=${ifDefined(name)}
                icon=${ifDefined(icon)}
            ></ak-app-icon>`,
        ),
};
