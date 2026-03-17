import "../Alert.js";

import { AKAlert, type IAlert } from "../Alert.js";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

type IAlertForTesting = IAlert & { message: string };

const metadata: Meta<AKAlert> = {
    title: "Elements/<ak-alert>",
    component: "ak-alert",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component: /* md */ `
# Alerts

Alerts are in-page elements intended to draw the user's attention and alert them to important
details. Alerts are used alongside form elements to warn users of potential mistakes they can
make, as well as in in-line documentation.

## Usage

\`\`\`Typescript
import "#elements/Alert";
\`\`\`

Note that the content of an alert _must_ be a valid HTML component; plain text does not work here.

\`\`\`html
<ak-alert><p>This is the content of your alert!</p></ak-alert>
\`\`\`
`,
            },
        },
    },
    argTypes: {
        inline: { control: "boolean" },
        level: { control: "text" },
        icon: { control: "text" },
        // @ts-expect-error Typescript is unaware that arguments for components
        // are treated as properties, and properties are typically renamed to lower case,
        // even if the variable is not.
        message: { control: "text" },
    },
};

export default metadata;

export const DefaultStory: StoryObj = {
    args: {
        inline: false,
        message: "You should be alarmed.",
    },

    // @ts-expect-error Storybook cannot infer the type here.
    render: ({ inline, level, icon, message }: IAlertForTesting) => {
        return html`
            <style>
                ak-alert {
                    display: inline-block;
                    width: 32rem;
                    max-width: 32rem;
                }
            </style>
            <ak-alert level=${ifDefined(level)} ?inline=${inline} icon=${ifDefined(icon)}>
                <p>${message}</p>
            </ak-alert>
        `;
    },
};

export const SuccessAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ level: "success", message: "He's a tribute to your genius!" } },
};

export const InfoAlert = {
    ...DefaultStory,
    args: {
        ...DefaultStory,
        ...{ level: "info", icon: "fa-coffee", message: "It is time for coffee." },
    },
};

export const DangerAlert = {
    ...DefaultStory,
    args: { ...DefaultStory, ...{ level: "danger", message: "Danger, Will Robinson!  Danger!" } },
};
