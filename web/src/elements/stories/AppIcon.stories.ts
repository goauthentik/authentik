import { PFSize } from "@goauthentik/common/enums.js";
import type { Meta, StoryObj } from "@storybook/web-components";

import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import "../AppIcon";
import { AppIcon } from "../AppIcon";

const sizeOptions = Array.from(Object.values(PFSize));

const metadata: Meta<AppIcon> = {
    title: "Elements / <ak-app-icon>",
    component: "ak-app-icon",
    parameters: {
        docs: {
            description: {
                component: "A small card displaying an application icon",
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

const container = (testItem: TemplateResult) =>
    html` <div style="background: #f0f0f0; padding: 1em">
        <style>
            li {
                display: block;
            }
            p {
                margin-top: 1em;
            }
        </style>
        ${testItem}
    </div>`;

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
